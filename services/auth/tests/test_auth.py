"""
Auth Service Tests
------------------
Run: pytest tests/ -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


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
    assert r.json()["service"] == "auth"
    assert r.json()["status"] == "ok"


# ── Registration validation ───────────────────────────────────────────────────

@pytest.mark.anyio
async def test_register_short_password():
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/register", json={"email": "a@b.sk", "password": "short"})

    assert r.status_code == 422


@pytest.mark.anyio
async def test_register_invalid_email():
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/register", json={"email": "notanemail", "password": "heslo1234"})

    assert r.status_code == 422


# ── Register success ──────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_register_success():
    from httpx import AsyncClient, ASGITransport
    from database import get_db

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def override_db():
        yield mock_db

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()), \
         patch("main._bootstrap_new_user", new_callable=AsyncMock):
        from main import app
        app.dependency_overrides[get_db] = override_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/register", json={"email": "new@test.sk", "password": "heslo1234"})
        app.dependency_overrides.clear()

    assert r.status_code == 201
    assert "access_token" in r.json()
    assert "refresh_token" in r.json()


# ── Login wrong password ──────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_login_wrong_password():
    from httpx import AsyncClient, ASGITransport
    from database import get_db, User, AccountType
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

    async def override_db():
        yield mock_db

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        app.dependency_overrides[get_db] = override_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/login", json={"email": "test@test.sk", "password": "wrongpassword"})
        app.dependency_overrides.clear()

    assert r.status_code == 401


# ── Token verification ────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_verify_valid_token():
    from httpx import AsyncClient, ASGITransport
    from security import create_access_token

    token = create_access_token("user-abc", "regular")

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/verify", json={"token": token})

    assert r.status_code == 200
    assert r.json()["valid"] is True
    assert r.json()["user_id"] == "user-abc"


@pytest.mark.anyio
async def test_verify_invalid_token():
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/verify", json={"token": "garbage.token.here"})

    assert r.status_code == 200
    assert r.json()["valid"] is False
