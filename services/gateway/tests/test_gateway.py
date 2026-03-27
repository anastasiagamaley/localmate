"""
Gateway Service Tests
---------------------
Run: pytest tests/ -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health():
    from unittest.mock import AsyncMock, patch, MagicMock
    from httpx import AsyncClient, ASGITransport

    mock_http = MagicMock()
    mock_http.aclose = AsyncMock()

    with patch("main.http_client", mock_http):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/health")

    assert r.status_code == 200
    assert r.json()["service"] == "gateway"


# ── Public routes ─────────────────────────────────────────────────────────────

def test_public_routes_list():
    from config import get_config
    cfg = get_config()
    public = cfg.public_routes
    assert "/auth/register" in public
    assert "/auth/login" in public
    assert "/auth/refresh" in public
    assert "/health" in public


def test_is_public_helper():
    from main import _is_public
    assert _is_public("/health") is True
    assert _is_public("/auth/register") is True
    assert _is_public("/auth/login") is True
    assert _is_public("/users/me") is False
    assert _is_public("/search/") is False
    assert _is_public("/tokens/balance") is False
    assert _is_public("/gigs/my") is False


# ── JWT protection ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_protected_route_without_token_returns_401():
    from unittest.mock import MagicMock, AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    mock_http = MagicMock()
    mock_http.aclose = AsyncMock()

    with patch("main.http_client", mock_http):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/users/me")  # no Authorization header

    assert r.status_code == 401


@pytest.mark.anyio
async def test_protected_route_with_invalid_token_returns_401():
    from unittest.mock import MagicMock, AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    mock_http = MagicMock()
    mock_http.aclose = AsyncMock()
    mock_http.post = AsyncMock(return_value=MagicMock(
        json=lambda: {"valid": False}
    ))

    with patch("main.http_client", mock_http):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/users/me", headers={"Authorization": "Bearer invalid.token"})

    assert r.status_code == 401


@pytest.mark.anyio
async def test_unknown_service_returns_404():
    from unittest.mock import MagicMock, AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    mock_http = MagicMock()
    mock_http.aclose = AsyncMock()
    mock_http.post = AsyncMock(return_value=MagicMock(
        json=lambda: {"valid": True, "user_id": "user-1", "account_type": "regular"}
    ))

    with patch("main.http_client", mock_http):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(
                "/nonexistent/endpoint",
                headers={"Authorization": "Bearer sometoken"}
            )

    assert r.status_code == 404


# ── Routes config ─────────────────────────────────────────────────────────────

def test_all_services_in_routes():
    """All services must be registered in gateway routes."""
    from main import ROUTES
    required = ["/auth", "/users", "/search", "/tokens", "/vendors", "/gigs"]
    for route in required:
        assert route in ROUTES, f"Missing route: {route}"
