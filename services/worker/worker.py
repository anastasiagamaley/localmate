"""
Celery Worker — background tasks for LocalMate.

Tasks:
  - award_xp_for_gig  : called when a gig is marked complete → hits users service
  - send_notification : future placeholder for email/push notifications

Usage from any service:
    from celery_client import award_xp_for_gig
    award_xp_for_gig.delay(provider_user_id="abc-123")
"""
import logging
import httpx
from celery import Celery
from pydantic_settings import BaseSettings
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerConfig(BaseSettings):
    redis_url: str = "redis://redis:6379/0"
    users_service_url: str = "http://users:8002"
    tokens_service_url: str = "http://tokens:8004"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> WorkerConfig:
    return WorkerConfig()


cfg = get_config()

# ─── Celery app ───────────────────────────────────────────────────────────────

app = Celery(
    "localmate_worker",
    broker=cfg.redis_url,
    backend=cfg.redis_url,
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Bratislava",
    enable_utc=True,
    # Retry failed tasks up to 3 times with exponential backoff
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_max_retries=3,
)


# ─── Tasks ────────────────────────────────────────────────────────────────────

@app.task(bind=True, max_retries=3, default_retry_delay=10)
def award_xp_for_gig(self, provider_user_id: str, gig_id: str):
    """
    Award XP to a provider after their gig is completed.
    Triggered by: POST /gigs/{gig_id}/complete (future gigs service).
    """
    logger.info(f"[award_xp_for_gig] provider={provider_user_id} gig={gig_id}")
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{cfg.users_service_url}/internal/gig-complete",
                json={"user_id": provider_user_id},
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                f"[award_xp_for_gig] ✅ XP awarded | "
                f"level={data.get('level')} level_name={data.get('level_name')} "
                f"gigs={data.get('gigs_completed')}"
            )
            return data
    except Exception as exc:
        logger.error(f"[award_xp_for_gig] ❌ failed: {exc}")
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification(self, user_id: str, title: str, body: str, channel: str = "email"):
    """
    Placeholder for future push/email notifications.
    Channels: email | push | sms
    """
    logger.info(f"[send_notification] user={user_id} channel={channel} title={title!r}")
    # TODO: integrate with SendGrid / Firebase Cloud Messaging
    return {"sent": True, "channel": channel}


@app.task
def health_check():
    """Periodic heartbeat — useful for monitoring."""
    logger.info("[health_check] Worker alive ✅")
    return "ok"


# ─── Periodic tasks (beat schedule) ──────────────────────────────────────────

app.conf.beat_schedule = {
    "worker-heartbeat": {
        "task": "worker.health_check",
        "schedule": 60.0,  # every 60 seconds
    },
}
