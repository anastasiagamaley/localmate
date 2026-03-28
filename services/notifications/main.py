import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from config import get_config
from sender import EmailSender
from templates import (
    welcome_email, returning_user_email, verify_email,
    gig_created_provider, gig_completed_provider, gig_completed_client,
    gig_cancelled, contact_opened_provider,
    low_tokens_warning, level_up_email,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cfg = get_config()

email_sender: Optional[EmailSender] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global email_sender
    email_sender = EmailSender(
        api_key=cfg.resend_api_key,
        from_email=cfg.from_email,
        from_name=cfg.from_name,
        environment=cfg.environment,
    )
    logger.info("Notifications service ready")
    yield


app = FastAPI(
    title="LocalMate — Notifications Service",
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
    return {"service": "notifications", "status": "ok"}


# ─── Schemas ──────────────────────────────────────────────────────────────────

class WelcomePayload(BaseModel):
    email: str
    name: str = ""
    tokens: int = 50
    is_returning: bool = False


class VerifyPayload(BaseModel):
    email: str
    name: str = ""
    verify_url: str


class GigCreatedPayload(BaseModel):
    provider_email: str
    provider_name: str = ""
    client_name: str = ""
    gig_title: str
    gig_price: int
    gig_id: str


class GigCompletedProviderPayload(BaseModel):
    provider_email: str
    provider_name: str = ""
    gig_title: str
    tokens_earned: int
    new_level: str = ""


class GigCompletedClientPayload(BaseModel):
    client_email: str
    client_name: str = ""
    gig_title: str
    tokens_spent: int


class GigCancelledPayload(BaseModel):
    recipient_email: str
    recipient_name: str = ""
    gig_title: str
    cancelled_by: str = ""
    reason: str = ""


class ContactOpenedPayload(BaseModel):
    provider_email: str
    provider_name: str = ""


class LowTokensPayload(BaseModel):
    email: str
    name: str = ""
    balance: int


class LevelUpPayload(BaseModel):
    email: str
    name: str = ""
    new_level: str
    gigs_count: int


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/welcome")
async def send_welcome(p: WelcomePayload):
    if p.is_returning:
        subject, html = returning_user_email(p.name, cfg.app_url)
    else:
        subject, html = welcome_email(p.name, p.tokens, cfg.app_url)
    ok = await email_sender.send(p.email, subject, html)
    return {"sent": ok}


@app.post("/verify")
async def send_verify(p: VerifyPayload):
    subject, html = verify_email(p.name, p.verify_url, cfg.app_url)
    ok = await email_sender.send(p.email, subject, html)
    return {"sent": ok}


@app.post("/gig-created")
async def send_gig_created(p: GigCreatedPayload):
    subject, html = gig_created_provider(
        p.provider_name, p.client_name,
        p.gig_title, p.gig_price, p.gig_id, cfg.app_url
    )
    ok = await email_sender.send(p.provider_email, subject, html)
    return {"sent": ok}


@app.post("/gig-completed-provider")
async def send_gig_completed_provider(p: GigCompletedProviderPayload):
    subject, html = gig_completed_provider(
        p.provider_name, p.gig_title,
        p.tokens_earned, p.new_level, cfg.app_url
    )
    ok = await email_sender.send(p.provider_email, subject, html)
    return {"sent": ok}


@app.post("/gig-completed-client")
async def send_gig_completed_client(p: GigCompletedClientPayload):
    subject, html = gig_completed_client(
        p.client_name, p.gig_title, p.tokens_spent, cfg.app_url
    )
    ok = await email_sender.send(p.client_email, subject, html)
    return {"sent": ok}


@app.post("/gig-cancelled")
async def send_gig_cancelled(p: GigCancelledPayload):
    subject, html = gig_cancelled(
        p.recipient_name, p.gig_title,
        p.cancelled_by, p.reason, cfg.app_url
    )
    ok = await email_sender.send(p.recipient_email, subject, html)
    return {"sent": ok}


@app.post("/contact-opened")
async def send_contact_opened(p: ContactOpenedPayload):
    subject, html = contact_opened_provider(p.provider_name, cfg.app_url)
    ok = await email_sender.send(p.provider_email, subject, html)
    return {"sent": ok}


@app.post("/low-tokens")
async def send_low_tokens(p: LowTokensPayload):
    subject, html = low_tokens_warning(p.name, p.balance, cfg.app_url)
    ok = await email_sender.send(p.email, subject, html)
    return {"sent": ok}


@app.post("/level-up")
async def send_level_up(p: LevelUpPayload):
    subject, html = level_up_email(p.name, p.new_level, p.gigs_count, cfg.app_url)
    ok = await email_sender.send(p.email, subject, html)
    return {"sent": ok}
