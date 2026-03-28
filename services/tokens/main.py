import logging
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from config import get_config
from database import get_db, create_tables, Wallet, Transaction, TxType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cfg = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    logger.info("Tokens service ready")
    yield


app = FastAPI(title="LocalMate — Tokens Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_caller_id(x_user_id: Optional[str] = Header(None)) -> Optional[str]:
    return x_user_id


# ─── Schemas ──────────────────────────────────────────────────────────────────

class WelcomePayload(BaseModel):
    user_id: str
    amount: int = 50


class BalanceResponse(BaseModel):
    user_id: str
    balance: int


class OpenContactRequest(BaseModel):
    target_user_id: str  # whose contact we're opening


class PayGigRequest(BaseModel):
    provider_id: str
    amount: int
    description: str = "Platba za službu"


class TxOut(BaseModel):
    id: str
    amount: int
    tx_type: str
    description: str
    created_at: str


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"service": "tokens", "status": "ok"}


# ─── Internal: grant welcome tokens after registration ───────────────────────

@app.post("/internal/welcome", status_code=201)
async def grant_welcome(payload: WelcomePayload, db: AsyncSession = Depends(get_db)):
    # Idempotent — skip if wallet already exists
    result = await db.execute(select(Wallet).where(Wallet.user_id == payload.user_id))
    if result.scalar_one_or_none():
        return {"ok": True, "note": "wallet already exists"}

    wallet = Wallet(user_id=payload.user_id, balance=payload.amount)
    db.add(wallet)

    tx = Transaction(
        user_id=payload.user_id,
        amount=payload.amount,
        tx_type=TxType.welcome,
        description=f"Uvítací bonus +{payload.amount} tokenov",
    )
    db.add(tx)
    await db.commit()
    logger.info(f"Granted {payload.amount} welcome tokens to {payload.user_id}")
    return {"ok": True, "balance": payload.amount}


# ─── Get balance ──────────────────────────────────────────────────────────────

@app.get("/balance", response_model=BalanceResponse)
async def get_balance(
    caller_id: Optional[str] = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    if not caller_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    wallet = await _wallet_or_404(caller_id, db)
    return BalanceResponse(user_id=caller_id, balance=wallet.balance)


# ─── Open contact (costs tokens) ─────────────────────────────────────────────

@app.post("/open-contact")
async def open_contact(
    payload: OpenContactRequest,
    caller_id: Optional[str] = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    if not caller_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if caller_id == payload.target_user_id:
        raise HTTPException(status_code=400, detail="Cannot open your own contact")

    wallet = await _wallet_or_404(caller_id, db)
    cost = cfg.contact_open_cost

    if wallet.balance < cost:
        raise HTTPException(
            status_code=402,
            detail=f"Nedostatok tokenov. Potrebuješ {cost} LM, máš {wallet.balance} LM.",
        )

    wallet.balance -= cost

    tx = Transaction(
        user_id=caller_id,
        counterpart_id=payload.target_user_id,
        amount=-cost,
        tx_type=TxType.contact,
        description=f"Otvorenie kontaktu −{cost} LM",
    )
    db.add(tx)
    await db.commit()

    logger.info(f"User {caller_id} opened contact of {payload.target_user_id} for {cost} tokens")

    # Notify provider (fire-and-forget, non-critical)
    await _notify_contact_opened(payload.target_user_id)

    return {"ok": True, "spent": cost, "new_balance": wallet.balance}


async def _notify_contact_opened(provider_id: str):
    """Tell provider someone viewed their contact."""
    try:
        import httpx as _httpx
        from config import get_config as _cfg
        cfg = _cfg()
        notifications_url = getattr(cfg, "notifications_service_url", "http://notifications:8007")
        users_url = getattr(cfg, "users_service_url", "http://users:8002")

        async with _httpx.AsyncClient(timeout=3.0) as client:
            # Get provider profile
            resp = await client.get(f"{users_url}/{provider_id}")
            if resp.status_code == 200:
                data = resp.json()
                email = data.get("email", "")
                name = data.get("name", "")
                if email:
                    await client.post(
                        f"{notifications_url}/contact-opened",
                        json={"provider_email": email, "provider_name": name},
                    )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Contact opened notification failed: {e}")


# ─── Pay for a gig ────────────────────────────────────────────────────────────

@app.post("/pay-gig")
async def pay_gig(
    payload: PayGigRequest,
    caller_id: Optional[str] = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
):
    if not caller_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    client_wallet = await _wallet_or_404(caller_id, db)
    if client_wallet.balance < payload.amount:
        raise HTTPException(status_code=402, detail="Nedostatok tokenov")

    # Deduct from client
    client_wallet.balance -= payload.amount
    db.add(Transaction(
        user_id=caller_id,
        counterpart_id=payload.provider_id,
        amount=-payload.amount,
        tx_type=TxType.payment,
        description=payload.description,
    ))

    # Credit to provider
    provider_wallet = await _wallet_or_404(payload.provider_id, db)
    provider_wallet.balance += payload.amount
    db.add(Transaction(
        user_id=payload.provider_id,
        counterpart_id=caller_id,
        amount=payload.amount,
        tx_type=TxType.payment,
        description=f"Príjem za gig: {payload.description}",
    ))

    await db.commit()
    return {"ok": True, "transferred": payload.amount, "new_balance": client_wallet.balance}


# ─── Transaction history ──────────────────────────────────────────────────────

@app.get("/history", response_model=List[TxOut])
async def get_history(
    caller_id: Optional[str] = Depends(get_caller_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    if not caller_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == caller_id)
        .order_by(desc(Transaction.created_at))
        .limit(limit)
    )
    txs = result.scalars().all()
    return [
        TxOut(
            id=tx.id,
            amount=tx.amount,
            tx_type=tx.tx_type.value,
            description=tx.description,
            created_at=tx.created_at.isoformat(),
        )
        for tx in txs
    ]


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _wallet_or_404(user_id: str, db: AsyncSession) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet
