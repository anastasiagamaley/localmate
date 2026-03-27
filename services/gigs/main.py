import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List

import httpx
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from config import get_config
from database import get_db, create_tables, Gig, GigStatus
from schemas import (
    GigCreate, GigOut, GigSummary, CancelRequest,
    PriceCheckRequest, PriceCheckResponse,
)
from pricing import PricingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cfg = get_config()

pricing = PricingEngine(
    gemini_api_key=cfg.gemini_api_key,
    provider=cfg.ai_provider,
)

http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    await create_tables()
    http_client = httpx.AsyncClient(timeout=10.0)
    logger.info("Gigs service ready")
    yield
    await http_client.aclose()


app = FastAPI(title="LocalMate — Gigs Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_caller_id(x_user_id: Optional[str] = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return x_user_id


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"service": "gigs", "status": "ok"}


# ─── AI Price check ───────────────────────────────────────────────────────────

@app.post("/price-check", response_model=PriceCheckResponse)
async def price_check(
    payload: PriceCheckRequest,
    caller_id: str = Depends(get_caller_id),
):
    """
    Before creating a gig, client asks AI: is this price fair?
    Returns recommended range + warning if price looks suspicious.
    """
    result = await pricing.get_price_recommendation(
        title=payload.title,
        description=payload.description,
        proposed_price=payload.proposed_price,
    )
    return PriceCheckResponse(
        proposed_price=payload.proposed_price,
        **result,
    )


# ─── Create gig ───────────────────────────────────────────────────────────────

@app.post("/", response_model=GigOut, status_code=201)
async def create_gig(
    payload: GigCreate,
    caller_id: str = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    if caller_id == payload.provider_id:
        raise HTTPException(status_code=400, detail="Nemôžeš vytvoriť gig sám pre seba")

    # ── Anti-laundering checks ────────────────────────────────────────────────

    # 1. Absolute maximum
    if payload.price_tokens > cfg.max_gig_tokens:
        raise HTTPException(
            status_code=400,
            detail=f"Maximálna cena giga je {cfg.max_gig_tokens} LM tokenov",
        )

    # 2. New user limit — get provider's gig count
    provider_gigs = await db.execute(
        select(Gig).where(
            Gig.provider_id == payload.provider_id,
            Gig.status == GigStatus.completed,
        )
    )
    provider_completed = len(provider_gigs.scalars().all())

    if (
        provider_completed < cfg.new_user_gig_threshold
        and payload.price_tokens > cfg.new_user_max_tokens
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Poskytovateľ má menej ako {cfg.new_user_gig_threshold} dokončených gigov. "
                f"Maximálna cena je {cfg.new_user_max_tokens} LM."
            ),
        )

    # 3. AI price validation + flag suspicious
    price_check = await pricing.get_price_recommendation(
        title=payload.title,
        description=payload.description,
        proposed_price=payload.price_tokens,
    )

    price_flagged = False
    flag_reason = ""

    if not price_check["is_reasonable"]:
        price_flagged = True
        flag_reason = price_check.get("warning", "Podozrivo vysoká cena")
        logger.warning(
            f"FLAGGED GIG: client={caller_id} provider={payload.provider_id} "
            f"price={payload.price_tokens} reason={flag_reason}"
        )

    gig = Gig(
        client_id=caller_id,
        provider_id=payload.provider_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        price_tokens=payload.price_tokens,
        recommended_min=payload.recommended_min or price_check["recommended_min"],
        recommended_max=payload.recommended_max or price_check["recommended_max"],
        price_flagged=price_flagged,
        flag_reason=flag_reason,
        client_lat=payload.client_lat,
        client_lon=payload.client_lon,
        # Flagged gigs are frozen until manual review
        status=GigStatus.flagged if price_flagged else GigStatus.pending,
    )

    db.add(gig)
    await db.commit()
    await db.refresh(gig)

    logger.info(
        f"Gig created: {gig.id} | {gig.title} | "
        f"{gig.price_tokens} LM | status={gig.status}"
    )
    return gig


# ─── My gigs ─────────────────────────────────────────────────────────────────

@app.get("/my", response_model=List[GigSummary])
async def my_gigs(
    caller_id: str = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
):
    """Returns all gigs where caller is client OR provider."""
    query = select(Gig).where(
        or_(Gig.client_id == caller_id, Gig.provider_id == caller_id)
    )
    if status:
        query = query.where(Gig.status == status)

    query = query.order_by(Gig.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


# ─── Get single gig ───────────────────────────────────────────────────────────

@app.get("/{gig_id}", response_model=GigOut)
async def get_gig(
    gig_id: str,
    caller_id: str = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    gig = await _get_gig_or_404(gig_id, db)
    # Only participants can see the gig
    if caller_id not in (gig.client_id, gig.provider_id):
        raise HTTPException(status_code=403, detail="Nemáš prístup k tomuto gigu")
    return gig


# ─── Accept gig (provider) ────────────────────────────────────────────────────

@app.post("/{gig_id}/accept", response_model=GigOut)
async def accept_gig(
    gig_id: str,
    caller_id: str = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    gig = await _get_gig_or_404(gig_id, db)

    if gig.provider_id != caller_id:
        raise HTTPException(status_code=403, detail="Iba poskytovateľ môže prijať gig")
    if gig.status != GigStatus.pending:
        raise HTTPException(status_code=400, detail=f"Gig je v stave '{gig.status}', nemožno prijať")

    gig.status = GigStatus.accepted
    gig.accepted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(gig)

    logger.info(f"Gig accepted: {gig_id} by provider {caller_id}")
    return gig


# ─── Complete gig (client confirms) ──────────────────────────────────────────

@app.post("/{gig_id}/complete", response_model=GigOut)
async def complete_gig(
    gig_id: str,
    caller_id: str = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    gig = await _get_gig_or_404(gig_id, db)

    if gig.client_id != caller_id:
        raise HTTPException(status_code=403, detail="Iba klient môže potvrdiť dokončenie")
    if gig.status != GigStatus.accepted:
        raise HTTPException(status_code=400, detail=f"Gig musí byť 'accepted', teraz je '{gig.status}'")

    # 1. Transfer tokens: client → provider
    await _transfer_tokens(
        client_id=gig.client_id,
        provider_id=gig.provider_id,
        amount=gig.price_tokens,
        description=f"Platba za gig: {gig.title}",
    )

    # 2. Award XP to provider via users service
    await _award_xp(provider_id=gig.provider_id, gig_id=gig.id)

    # 3. Mark complete
    gig.status = GigStatus.completed
    gig.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(gig)

    logger.info(
        f"Gig completed: {gig_id} | "
        f"{gig.price_tokens} LM transferred to {gig.provider_id}"
    )
    return gig


# ─── Cancel gig ───────────────────────────────────────────────────────────────

@app.post("/{gig_id}/cancel", response_model=GigOut)
async def cancel_gig(
    gig_id: str,
    payload: CancelRequest,
    caller_id: str = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    gig = await _get_gig_or_404(gig_id, db)

    if caller_id not in (gig.client_id, gig.provider_id):
        raise HTTPException(status_code=403, detail="Nemáš prístup k tomuto gigu")
    if gig.status in (GigStatus.completed, GigStatus.cancelled):
        raise HTTPException(status_code=400, detail=f"Gig už je '{gig.status}'")

    gig.status = GigStatus.cancelled
    gig.cancelled_at = datetime.now(timezone.utc)
    if payload.reason:
        gig.flag_reason = f"Zrušené: {payload.reason}"

    await db.commit()
    await db.refresh(gig)

    logger.info(f"Gig cancelled: {gig_id} by {caller_id} | reason: {payload.reason}")
    return gig


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_gig_or_404(gig_id: str, db: AsyncSession) -> Gig:
    result = await db.execute(select(Gig).where(Gig.id == gig_id))
    gig = result.scalar_one_or_none()
    if not gig:
        raise HTTPException(status_code=404, detail="Gig nenájdený")
    return gig


async def _transfer_tokens(client_id: str, provider_id: str, amount: int, description: str):
    """Call tokens service to transfer tokens from client to provider."""
    try:
        # We call tokens service as the client (using internal header)
        resp = await http_client.post(
            f"{cfg.tokens_service_url}/pay-gig",
            json={
                "provider_id": provider_id,
                "amount": amount,
                "description": description,
            },
            headers={"X-User-Id": client_id},
        )
        resp.raise_for_status()
        logger.info(f"Tokens transferred: {amount} LM from {client_id} to {provider_id}")
    except Exception as e:
        logger.error(f"Token transfer failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Platba tokenmi zlyhala. Skúste znova.",
        )


async def _award_xp(provider_id: str, gig_id: str):
    """Call users service to award XP to provider."""
    try:
        resp = await http_client.post(
            f"{cfg.users_service_url}/internal/gig-complete",
            json={"user_id": provider_id},
        )
        resp.raise_for_status()
    except Exception as e:
        # XP failure is non-critical — log but don't fail the completion
        logger.warning(f"XP award failed for {provider_id}: {e}")
