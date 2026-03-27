"""
Auth Service Tests
------------------
Run: pytest tests/ -v
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """In-memory test client — no real DB needed."""
    # Patch DB and external calls before importing app
    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("main._bootstrap_new_user", new_callable=AsyncMock):

        from main import app
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c


@pytest.fixture
def mock_user():
    return {"email": "test@localmate.sk", "password": "heslo1234"}


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "auth"
    assert r.json()["status"] == "ok"


# ── Security utils ────────────────────────────────────────────────────────────

def test_password_hash_and_verify():
    from security import hash_password, verify_password
    hashed = hash_password("supersecret")
    assert verify_password("supersecret", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_access_token_contains_user_id():
    from security import create_access_token, decode_token
    token = create_access_token("user-123", "regular")
    data = decode_token(token)
    assert data is not None
    assert data["sub"] == "user-123"
    assert data["account_type"] == "regular"
    assert data["type"] == "access"


def test_refresh_token_type():
    from security import create_refresh_token, decode_token
    token = create_refresh_token("user-456")
    data = decode_token(token)
    assert data["type"] == "refresh"
    assert data["sub"] == "user-456"


def test_invalid_token_returns_none():
    from security import decode_token
    assert decode_token("not.a.valid.token") is None
    assert decode_token("") is None


# ── Registration ──────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_register_success(mock_user):
    from main import app
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # email not taken
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    with patch("main.get_db", return_value=mock_db), \
         patch("main._bootstrap_new_user", new_callable=AsyncMock), \
         patch("database.create_tables", new_callable=AsyncMock):

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/register", json=mock_user)

    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_register_short_password():
    from main import app
    with patch("database.create_tables", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/register", json={"email": "a@b.sk", "password": "short"})
    assert r.status_code == 422  # validation error


@pytest.mark.anyio
async def test_register_invalid_email():
    from main import app
    with patch("database.create_tables", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/register", json={"email": "notanemail", "password": "heslo1234"})
    assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_login_wrong_password():
    from main import app
    from unittest.mock import AsyncMock, MagicMock, patch
    from database import User, AccountType
    from security import hash_password

    fake_user = MagicMock(spec=User)
    fake_user.password_hash = hash_password("correctpassword")
    fake_user.is_active = True
    fake_user.account_type = AccountType.regular
    fake_user.id = "user-999"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_user

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("main.get_db", return_value=mock_db), \
         patch("database.create_tables", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/login", json={"email": "test@test.sk", "password": "wrongpassword"})

    assert r.status_code == 401


# ── Token verification ────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_verify_valid_token():
    from main import app
    from security import create_access_token

    token = create_access_token("user-abc", "regular")

    with patch("database.create_tables", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/verify", json={"token": token})

    assert r.status_code == 200
    assert r.json()["valid"] is True
    assert r.json()["user_id"] == "user-abc"


@pytest.mark.anyio
async def test_verify_invalid_token():
    from main import app
    with patch("database.create_tables", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/verify", json={"token": "garbage.token.here"})

    assert r.status_code == 200
    assert r.json()["valid"] is False
