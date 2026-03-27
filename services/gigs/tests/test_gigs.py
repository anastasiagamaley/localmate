"""
Gigs Service Tests
------------------
Run: pytest tests/ -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Pricing engine ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_pricing_fallback_reasonable_price():
    from pricing import PricingEngine
    engine = PricingEngine()  # no API key = fallback mode
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
        proposed_price=99999,  # obviously too much
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
    from unittest.mock import AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/health")

    assert r.status_code == 200
    assert r.json()["service"] == "gigs"


# ── Price check endpoint ──────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_price_check_endpoint():
    from unittest.mock import AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
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
    assert "is_reasonable" in data
    assert data["proposed_price"] == 80


# ── Create gig ────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_gig_cannot_gig_yourself():
    from unittest.mock import AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "user-1"}
        ) as c:
            r = await c.post("/", json={
                "provider_id": "user-1",  # same as caller
                "title": "Test",
                "price_tokens": 100,
            })

    assert r.status_code == 400


@pytest.mark.anyio
async def test_create_gig_exceeds_absolute_max():
    from unittest.mock import AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "client-1"}
        ) as c:
            r = await c.post("/", json={
                "provider_id": "provider-1",
                "title": "Test",
                "price_tokens": 999999,  # way over max_gig_tokens=5000
            })

    assert r.status_code == 400
    assert "5000" in r.json()["detail"]


@pytest.mark.anyio
async def test_create_gig_new_user_limit():
    """New provider (< 5 gigs) cannot receive gigs over 500 LM."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport

    # Mock: provider has 0 completed gigs
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []  # 0 completed gigs

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "client-1"}
        ) as c:
            r = await c.post("/", json={
                "provider_id": "new-provider",
                "title": "Test gig",
                "price_tokens": 1000,  # over new_user_max=500
            })

    assert r.status_code == 400
    assert "500" in r.json()["detail"]


# ── Gig state machine ─────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_only_provider_can_accept():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Gig, GigStatus

    fake_gig = MagicMock(spec=Gig)
    fake_gig.provider_id = "provider-1"
    fake_gig.client_id = "client-1"
    fake_gig.status = GigStatus.pending

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_gig

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "client-1"}  # client tries to accept = wrong
        ) as c:
            r = await c.post("/gig-123/accept")

    assert r.status_code == 403


@pytest.mark.anyio
async def test_only_client_can_complete():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Gig, GigStatus

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

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "provider-1"}  # provider tries to complete = wrong
        ) as c:
            r = await c.post("/gig-123/complete")

    assert r.status_code == 403


@pytest.mark.anyio
async def test_cannot_accept_completed_gig():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Gig, GigStatus

    fake_gig = MagicMock(spec=Gig)
    fake_gig.provider_id = "provider-1"
    fake_gig.client_id = "client-1"
    fake_gig.status = GigStatus.completed  # already done

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_gig

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "provider-1"}
        ) as c:
            r = await c.post("/gig-123/accept")

    assert r.status_code == 400
