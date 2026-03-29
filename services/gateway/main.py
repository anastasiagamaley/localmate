import logging
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cfg = get_config()

# Shared async HTTP client — reused across requests (connection pooling)
http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    # Single client with connection pooling — handles 5000 users efficiently
    http_client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=500, max_keepalive_connections=100),
    )
    logger.info("Gateway starting — HTTP client pool ready")
    yield
    await http_client.aclose()
    logger.info("Gateway shutting down")


app = FastAPI(
    title="LocalMate — API Gateway",
    version="0.1.0",
    description="Single entry point for all LocalMate services",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Route map: prefix → upstream service URL ────────────────────────────────
ROUTES = {
    "/auth":          cfg.auth_service_url,
    "/users":         cfg.users_service_url,
    "/search":        cfg.search_service_url,
    "/tokens":        cfg.tokens_service_url,
    "/vendors":       cfg.vendors_service_url,
    "/gigs":          cfg.gigs_service_url,
    "/notifications": cfg.notifications_service_url,
}


def _is_public(path: str) -> bool:
    for public in cfg.public_routes:
        if path.startswith(public):
            return True
    return False


async def _verify_jwt(token: str) -> Optional[dict]:
    """Ask auth service to validate the JWT. Returns user info or None."""
    try:
        resp = await http_client.post(
            f"{cfg.auth_service_url}/verify",
            json={"token": token},
            timeout=5.0,
        )
        data = resp.json()
        if data.get("valid"):
            return data
    except Exception as e:
        logger.error(f"JWT verification failed: {e}")
    return None


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"service": "gateway", "status": "ok", "version": "0.1.0"}


# ─── Main proxy handler ───────────────────────────────────────────────────────

@app.api_route(
    "/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy(service: str, path: str, request: Request):
    full_path = f"/{service}/{path}"

    # ── Auth check ────────────────────────────────────────────────────────────
    user_id: Optional[str] = None
    account_type: Optional[str] = None

    if not _is_public(full_path):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.split(" ", 1)[1]
        user_info = await _verify_jwt(token)
        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_id = user_info["user_id"]
        account_type = user_info["account_type"]

    # ── Route to upstream ─────────────────────────────────────────────────────
    upstream_base = ROUTES.get(f"/{service}")
    if not upstream_base:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    upstream_url = f"{upstream_base}/{path}"
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    # Build headers — forward user identity to downstream services
    headers = dict(request.headers)
    headers.pop("host", None)
    if user_id:
        headers["X-User-Id"] = user_id
        headers["X-Account-Type"] = account_type or ""

    body = await request.body()

    try:
        resp = await http_client.request(
            method=request.method,
            url=upstream_url,
            headers=headers,
            content=body,
        )
    except httpx.ConnectError:
        logger.error(f"Cannot connect to upstream: {upstream_url}")
        raise HTTPException(status_code=503, detail=f"Service '{service}' unavailable")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Service '{service}' timed out")

    # Strip hop-by-hop headers before returning
    excluded = {"transfer-encoding", "connection", "keep-alive", "upgrade", "date", "server"}
    response_headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() not in excluded
    }

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type"),
    )


# ─── Global error handler ─────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"},
    )


@app.options("/{service}/{path:path}")
async def options_handler(service: str, path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-User-Id, X-Account-Type",
        }
    )
