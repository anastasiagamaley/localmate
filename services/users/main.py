import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import get_config
from database import get_db, create_tables, Profile
from schemas import ProfileCreate, ProfileUpdate, ProfilePublic, GigCompleteRequest, XpResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cfg = get_config()


# ─── Level system ─────────────────────────────────────────────────────────────

LEVELS = [
    (cfg.level_master_min,   8, "Master 👑"),
    (cfg.level_platinum_min, 5, "Platinový 💎"),
    (cfg.level_gold_min,     3, "Zlatý 🏅"),
    (cfg.level_silver_min,   2, "Strieborný 🥈"),
    (cfg.level_bronze_min,   1, "Bronzový 🥉"),
]

LEVEL_THRESHOLDS = [
    (cfg.level_master_min,   300),
    (cfg.level_platinum_min, 100),
    (cfg.level_gold_min,     30),
    (cfg.level_silver_min,   10),
    (0,                      0),
]


def compute_level(gigs: int) -> tuple[int, str]:
    for min_gigs, level_num, name in LEVELS:
        if gigs >= min_gigs:
            return level_num, name
    return 1, "Bronzový 🥉"


def xp_to_next(gigs: int) -> int:
    """How many more gigs until next level."""
    for min_gigs, _, _ in LEVELS:
        if gigs < min_gigs:
            return min_gigs - gigs
    return 0  # already Master


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Users service starting...")
    await create_tables()
    yield
    logger.info("Users service shutting down")


app = FastAPI(title="LocalMate — Users Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_caller_id(x_user_id: Optional[str] = Header(None)) -> Optional[str]:
    return x_user_id


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"service": "users", "status": "ok"}


# ─── Internal: create profile after registration ──────────────────────────────

@app.post("/internal/create", status_code=201)
async def internal_create_profile(payload: ProfileCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Profile).where(Profile.user_id == payload.user_id))
    if existing.scalar_one_or_none():
        return {"ok": True, "note": "already exists"}

    profile = Profile(
        user_id=payload.user_id,
        email=payload.email,
        account_type=payload.account_type,
    )
    db.add(profile)
    await db.commit()
    logger.info(f"Profile created for user {payload.user_id}")
    return {"ok": True}


# ─── Get own profile ──────────────────────────────────────────────────────────

@app.get("/me", response_model=ProfilePublic)
async def get_my_profile(
    caller_id: Optional[str] = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    if not caller_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    profile = await _get_profile_or_404(caller_id, db)
    level_num, level_name = compute_level(profile.gigs_completed)
    return _to_public(profile, level_name)


# ─── Update own profile ───────────────────────────────────────────────────────

@app.patch("/me", response_model=ProfilePublic)
async def update_my_profile(
    payload: ProfileUpdate,
    caller_id: Optional[str] = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    if not caller_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    profile = await _get_profile_or_404(caller_id, db)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    _, level_name = compute_level(profile.gigs_completed)
    return _to_public(profile, level_name)


# ─── Get public profile by user_id ───────────────────────────────────────────

@app.get("/{user_id}", response_model=ProfilePublic)
async def get_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(user_id, db)
    _, level_name = compute_level(profile.gigs_completed)
    return _to_public(profile, level_name)


# ─── Internal: award XP after gig completion ─────────────────────────────────

@app.post("/internal/gig-complete")
async def gig_complete(payload: GigCompleteRequest, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(payload.user_id, db)

    profile.gigs_completed += 1
    profile.xp += cfg.xp_per_gig

    new_level, new_level_name = compute_level(profile.gigs_completed)
    leveled_up = new_level > profile.level
    profile.level = new_level

    await db.commit()
    await db.refresh(profile)

    logger.info(
        f"User {payload.user_id} completed gig #{profile.gigs_completed} "
        f"| +{cfg.xp_per_gig} XP | level {new_level} {'⬆️ LEVEL UP!' if leveled_up else ''}"
    )
    return XpResponse(
        user_id=payload.user_id,
        xp=profile.xp,
        level=new_level,
        level_name=new_level_name,
        gigs_completed=profile.gigs_completed,
        xp_to_next_level=xp_to_next(profile.gigs_completed),
    )


# ─── XP info endpoint ────────────────────────────────────────────────────────

@app.get("/{user_id}/xp", response_model=XpResponse)
async def get_xp(user_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(user_id, db)
    _, level_name = compute_level(profile.gigs_completed)
    return XpResponse(
        user_id=user_id,
        xp=profile.xp,
        level=profile.level,
        level_name=level_name,
        gigs_completed=profile.gigs_completed,
        xp_to_next_level=xp_to_next(profile.gigs_completed),
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_profile_or_404(user_id: str, db: AsyncSession) -> Profile:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


def _to_public(profile: Profile, level_name: str) -> ProfilePublic:
    return ProfilePublic(
        user_id=profile.user_id,
        name=profile.name,
        bio=profile.bio,
        city=profile.city,
        service_description=profile.service_description,
        tags=profile.tags,
        xp=profile.xp,
        level=profile.level,
        gigs_completed=str(profile.gigs_completed),
        account_type=profile.account_type,
        level_name=level_name,
        created_at=profile.created_at,
    )
