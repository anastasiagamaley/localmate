"""
Tokens Service Tests
--------------------
Run: pytest tests/ -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def anyio_backend():
    return "asyncio"


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
    assert r.json()["service"] == "tokens"


# ── Welcome tokens ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_welcome_tokens_granted():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # no wallet yet
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/internal/welcome", json={"user_id": "user-1", "amount": 50})

    assert r.status_code == 201
    assert r.json()["balance"] == 50


@pytest.mark.anyio
async def test_welcome_tokens_idempotent():
    """Calling welcome twice should not create duplicate wallet."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Wallet

    existing_wallet = MagicMock(spec=Wallet)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_wallet

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/internal/welcome", json={"user_id": "user-1", "amount": 50})

    assert r.status_code == 201
    assert "already exists" in r.json().get("note", "")


# ── Balance ───────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_balance_requires_auth():
    from unittest.mock import AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/balance")  # no X-User-Id header

    assert r.status_code == 401


@pytest.mark.anyio
async def test_get_balance_returns_amount():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Wallet

    fake_wallet = MagicMock(spec=Wallet)
    fake_wallet.balance = 150
    fake_wallet.user_id = "user-1"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_wallet

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "user-1"}
        ) as c:
            r = await c.get("/balance")

    assert r.status_code == 200
    assert r.json()["balance"] == 150


# ── Open contact ──────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_open_contact_deducts_tokens():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Wallet

    fake_wallet = MagicMock(spec=Wallet)
    fake_wallet.balance = 50
    fake_wallet.user_id = "client-1"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_wallet

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "client-1"}
        ) as c:
            r = await c.post("/open-contact", json={"target_user_id": "provider-1"})

    assert r.status_code == 200
    assert r.json()["spent"] == 5
    assert r.json()["new_balance"] == 45


@pytest.mark.anyio
async def test_open_contact_insufficient_tokens():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Wallet

    fake_wallet = MagicMock(spec=Wallet)
    fake_wallet.balance = 3  # not enough (need 5)
    fake_wallet.user_id = "poor-user"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_wallet

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main.get_db", return_value=mock_db):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "poor-user"}
        ) as c:
            r = await c.post("/open-contact", json={"target_user_id": "provider-1"})

    assert r.status_code == 402


@pytest.mark.anyio
async def test_cannot_open_own_contact():
    from unittest.mock import AsyncMock, patch
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock):
        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-User-Id": "user-1"}
        ) as c:
            r = await c.post("/open-contact", json={"target_user_id": "user-1"})

    assert r.status_code == 400
