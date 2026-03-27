import logging
import math
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from config import get_config
from database import get_db, create_tables, Profile
from ai_provider import get_ai_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cfg = get_config()

ai = get_ai_provider(
    cfg.ai_provider,
    gemini_api_key=cfg.gemini_api_key,
    openai_api_key=cfg.openai_api_key,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    logger.info(f"Search service ready | AI provider: {cfg.ai_provider}")
    yield


app = FastAPI(title="LocalMate — Search Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ──────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    lat: float
    lon: float
    max_distance_km: float = 20.0
    limit: int = 10


class ProviderResult(BaseModel):
    user_id: str
    name: str
    service_description: str
    tags: str
    city: str
    level: int
    level_name: str
    gigs_completed: int
    distance_km: float
    relevance_rank: int


class SearchResponse(BaseModel):
    query: str
    interpreted: dict
    results: List[ProviderResult]
    total: int


# ─── Haversine distance ───────────────────────────────────────────────────────

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two GPS points in kilometres."""
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


LEVEL_NAMES = {
    1: "Bronzový 🥉",
    2: "Strieborný 🥈",
    3: "Zlatý 🏅",
    4: "Zlatý 🏅",
    5: "Platinový 💎",
    6: "Platinový 💎",
    7: "Platinový 💎",
    8: "Master 👑",
}


def get_caller_id(x_user_id: Optional[str] = Header(None)) -> Optional[str]:
    return x_user_id


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"service": "search", "status": "ok", "ai_provider": cfg.ai_provider}


# ─── Main search endpoint ─────────────────────────────────────────────────────

@app.post("/", response_model=SearchResponse)
async def search(
    payload: SearchRequest,
    caller_id: Optional[str] = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    if not caller_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # 1. AI interprets the natural language query
    interpreted = await ai.interpret_query(payload.query)
    keywords = interpreted.get("keywords", payload.query.lower().split())
    logger.info(f"Search query='{payload.query}' interpreted={interpreted}")

    # 2. Fetch all profiles with location set (excluding self)
    result = await db.execute(
        select(Profile).where(
            and_(
                Profile.lat.isnot(None),
                Profile.lon.isnot(None),
                Profile.user_id != caller_id,
                Profile.service_description != "",
            )
        )
    )
    all_profiles = result.scalars().all()

    # 3. Filter by distance
    candidates = []
    for p in all_profiles:
        dist = haversine_km(payload.lat, payload.lon, p.lat, p.lon)
        if dist <= payload.max_distance_km:
            # Simple keyword pre-filter before expensive AI ranking
            searchable = f"{p.service_description} {p.tags} {p.name}".lower()
            if any(kw in searchable for kw in keywords):
                candidates.append({
                    "user_id": p.user_id,
                    "name": p.name,
                    "service_description": p.service_description,
                    "tags": p.tags,
                    "city": p.city,
                    "level": p.level,
                    "gigs_completed": p.gigs_completed,
                    "distance_km": round(dist, 2),
                })

    if not candidates:
        return SearchResponse(query=payload.query, interpreted=interpreted, results=[], total=0)

    # 4. AI re-ranks candidates by relevance
    ranked = await ai.rank_results(payload.query, candidates[: payload.limit * 2])
    ranked = ranked[: payload.limit]

    results = [
        ProviderResult(
            user_id=c["user_id"],
            name=c["name"],
            service_description=c["service_description"],
            tags=c["tags"],
            city=c["city"],
            level=c["level"],
            level_name=LEVEL_NAMES.get(c["level"], "Bronzový 🥉"),
            gigs_completed=c["gigs_completed"],
            distance_km=c["distance_km"],
            relevance_rank=i + 1,
        )
        for i, c in enumerate(ranked)
    ]

    return SearchResponse(
        query=payload.query,
        interpreted=interpreted,
        results=results,
        total=len(results),
    )
