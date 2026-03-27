"""
Gigs Service Tests
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Pricing engine (no DB needed) ────────────────────────────────────────────

@pytest.mark.anyio
async def test_pricing_fallback_reasonable_price():
    from pricing import PricingEngine
    engine = PricingEngine()
    result = await engine.get_price_recommendation(
        title="Oprava iPhone displeja",
        description="Výmena displeja iPhone 13",
        proposed_price=100,
    )
    assert result["recommended_min"] > 0
    assert result["recommended_max"] > result["recommended_min"]
    assert result["is_reasonable"] is True
    assert result["warning"] is None


@pytest.mark.anyio
async def test_pricing_flags_suspicious_price():
    from pricing import PricingEngine
    engine = PricingEngine()
    result = await engine.get_price_recommendation(
        title="Strihanie trávy",
        description="Kosenie malej záhrady",
        proposed_price=99999,
    )
    assert result["is_reasonable"] is False
    assert result["warning"] is not None


@pytest.mark.anyio
async def test_pricing_returns_explanation():
    from pricing import PricingEngine
    engine = PricingEngine()
    result = await engine.get_price_recommendation("Test", "", 50)
    assert len(result["ai_explanation"]) > 0


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health():
    from httpx import AsyncClient, ASGITransport
    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "gigs"


# ── Price check endpoint ──────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_price_check_endpoint():
    from httpx import AsyncClient, ASGITransport
    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test",
            headers={"X-User-Id": "user-1"}
        ) as c:
            r = await c.post("/price-check", json={
                "title": "Oprava počítača",
                "description": "Inštalácia Windows",
                "proposed_price": 80,
            })
    assert r.status_code == 200
    data = r.json()
    assert "recommended_min" in data
    assert "recommended_max" in data
    assert data["proposed_price"] == 80


# ── Validation ────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_gig_cannot_gig_yourself():
    from httpx import AsyncClient, ASGITransport
    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test",
            headers={"X-User-Id": "user-1"}
        ) as c:
            r = await c.post("/", json={
                "provider_id": "user-1",
                "title": "Test",
                "price_tokens": 100,
            })
    assert r.status_code == 400


@pytest.mark.anyio
async def test_create_gig_exceeds_absolute_max():
    from httpx import AsyncClient, ASGITransport
    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test",
            headers={"X-User-Id": "client-1"}
        ) as c:
            r = await c.post("/", json={
                "provider_id": "provider-1",
                "title": "Test",
                "price_tokens": 999999,
            })
    assert r.status_code == 400
    assert "5000" in r.json()["detail"]


# ── Gig state machine ─────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_only_provider_can_accept():
    from httpx import AsyncClient, ASGITransport
    from database import get_db, Gig, GigStatus

    fake_gig = MagicMock(spec=Gig)
    fake_gig.provider_id = "provider-1"
    fake_gig.client_id = "client-1"
    fake_gig.status = GigStatus.pending

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_gig
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def override_db():
        yield mock_db

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        app.dependency_overrides[get_db] = override_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test",
            headers={"X-User-Id": "client-1"}
        ) as c:
            r = await c.post("/gig-123/accept")
        app.dependency_overrides.clear()

    assert r.status_code == 403


@pytest.mark.anyio
async def test_only_client_can_complete():
    from httpx import AsyncClient, ASGITransport
    from database import get_db, Gig, GigStatus

    fake_gig = MagicMock(spec=Gig)
    fake_gig.provider_id = "provider-1"
    fake_gig.client_id = "client-1"
    fake_gig.status = GigStatus.accepted
    fake_gig.price_tokens = 100
    fake_gig.title = "Test"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_gig
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def override_db():
        yield mock_db

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        app.dependency_overrides[get_db] = override_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test",
            headers={"X-User-Id": "provider-1"}
        ) as c:
            r = await c.post("/gig-123/complete")
        app.dependency_overrides.clear()

    assert r.status_code == 403


@pytest.mark.anyio
async def test_cannot_accept_completed_gig():
    from httpx import AsyncClient, ASGITransport
    from database import get_db, Gig, GigStatus

    fake_gig = MagicMock(spec=Gig)
    fake_gig.provider_id = "provider-1"
    fake_gig.client_id = "client-1"
    fake_gig.status = GigStatus.completed

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_gig
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def override_db():
        yield mock_db

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        app.dependency_overrides[get_db] = override_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test",
            headers={"X-User-Id": "provider-1"}
        ) as c:
            r = await c.post("/gig-123/accept")
        app.dependency_overrides.clear()

    assert r.status_code == 400
