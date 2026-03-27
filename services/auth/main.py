import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import get_config
from database import get_db, create_tables, User, AccountType
from schemas import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, UserPublic, VerifyTokenRequest, VerifyTokenResponse,
)
from security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cfg = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Auth service starting up...")
    await create_tables()
    logger.info("Database tables ready")
    yield
    logger.info("Auth service shutting down")


app = FastAPI(
    title="LocalMate — Auth Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"service": "auth", "status": "ok", "version": "0.1.0"}


# ─── Register ────────────────────────────────────────────────────────────────

@app.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        account_type=payload.account_type,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Fire-and-forget: create profile + grant welcome tokens
    await _bootstrap_new_user(user.id, user.email, user.account_type.value)

    access = create_access_token(user.id, user.account_type.value)
    refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user_id=user.id,
        account_type=user.account_type.value,
    )


# ─── Login ───────────────────────────────────────────────────────────────────

@app.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    access = create_access_token(user.id, user.account_type.value)
    refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user_id=user.id,
        account_type=user.account_type.value,
    )


# ─── Refresh ─────────────────────────────────────────────────────────────────

@app.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == data["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or disabled")

    access = create_access_token(user.id, user.account_type.value)
    new_refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        user_id=user.id,
        account_type=user.account_type.value,
    )


# ─── Verify token (called by gateway) ────────────────────────────────────────

@app.post("/verify", response_model=VerifyTokenResponse)
async def verify_token(payload: VerifyTokenRequest):
    data = decode_token(payload.token)
    if not data or data.get("type") != "access":
        return VerifyTokenResponse(valid=False)
    return VerifyTokenResponse(
        valid=True,
        user_id=data["sub"],
        account_type=data.get("account_type"),
    )


# ─── Me ──────────────────────────────────────────────────────────────────────

@app.get("/me", response_model=UserPublic)
async def get_me(user_id: str, db: AsyncSession = Depends(get_db)):
    # user_id injected by gateway after JWT validation
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ─── Internal bootstrap ──────────────────────────────────────────────────────

async def _bootstrap_new_user(user_id: str, email: str, account_type: str):
    """
    After registration: create profile in users-service
    and grant welcome tokens in tokens-service.
    Uses httpx with timeout — failures are logged but don't break registration.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1. Create user profile
        try:
            await client.post(
                f"{cfg.users_service_url}/internal/create",
                json={"user_id": user_id, "email": email, "account_type": account_type},
            )
        except Exception as e:
            logger.warning(f"Could not create profile for {user_id}: {e}")

        # 2. Grant welcome tokens
        try:
            await client.post(
                f"{cfg.tokens_service_url}/internal/welcome",
                json={"user_id": user_id, "amount": cfg.welcome_tokens},
            )
        except Exception as e:
            logger.warning(f"Could not grant welcome tokens to {user_id}: {e}")
