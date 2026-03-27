"""
Users Service Tests
-------------------
Run: pytest tests/ -v
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── Level system ──────────────────────────────────────────────────────────────

def test_level_bronze_at_start():
    from main import compute_level
    level, name = compute_level(0)
    assert level == 1
    assert "Bronzový" in name


def test_level_silver_at_10_gigs():
    from main import compute_level
    level, name = compute_level(10)
    assert level == 2
    assert "Strieborný" in name


def test_level_gold_at_30_gigs():
    from main import compute_level
    level, name = compute_level(30)
    assert level == 3
    assert "Zlatý" in name


def test_level_platinum_at_100_gigs():
    from main import compute_level
    level, name = compute_level(100)
    assert level == 5
    assert "Platinový" in name


def test_level_master_at_300_gigs():
    from main import compute_level
    level, name = compute_level(300)
    assert level == 8
    assert "Master" in name


def test_level_does_not_decrease():
    from main import compute_level
    """More gigs = same or higher level, never lower."""
    prev_level = 0
    for gigs in [0, 5, 10, 29, 30, 99, 100, 299, 300, 500]:
        level, _ = compute_level(gigs)
        assert level >= prev_level
        prev_level = level


def test_xp_to_next_level_bronze():
    from main import xp_to_next
    # At 0 gigs, need 10 more for silver
    assert xp_to_next(0) == 10


def test_xp_to_next_level_silver():
    from main import xp_to_next
    # At 10 gigs (silver), need 20 more to reach gold (30)
    assert xp_to_next(10) == 20


def test_xp_to_next_level_master_is_zero():
    from main import xp_to_next
    # Master is max level
    assert xp_to_next(300) == 0
    assert xp_to_next(999) == 0


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health():
    from unittest.mock import AsyncMock, patch, MagicMock
    from httpx import AsyncClient, ASGITransport

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/health")

    assert r.status_code == 200
    assert r.json()["service"] == "users"


# ── Internal profile creation ─────────────────────────────────────────────────

@pytest.mark.anyio
async def test_internal_create_profile():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    async def override_get_db():
        yield mock_db

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        from database import get_db
        app.dependency_overrides[get_db] = override_get_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/internal/create", json={
                "user_id": "user-123",
                "email": "test@test.sk",
                "account_type": "regular"
            })
        app.dependency_overrides.clear()

    assert r.status_code == 201
    assert r.json()["ok"] is True


@pytest.mark.anyio
async def test_internal_create_profile_idempotent():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Profile

    existing = MagicMock(spec=Profile)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    async def override_get_db():
        yield mock_db

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        from database import get_db
        app.dependency_overrides[get_db] = override_get_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/internal/create", json={
                "user_id": "user-123",
                "email": "test@test.sk",
                "account_type": "regular"
            })
        app.dependency_overrides.clear()

    assert r.status_code == 201
    assert "already exists" in r.json().get("note", "")


@pytest.mark.anyio
async def test_gig_complete_awards_xp():
    from unittest.mock import AsyncMock, MagicMock, patch
    from httpx import AsyncClient, ASGITransport
    from database import Profile

    fake_profile = MagicMock(spec=Profile)
    fake_profile.gigs_completed = 9
    fake_profile.xp = 90
    fake_profile.level = 1
    fake_profile.user_id = "provider-1"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_profile

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def override_get_db():
        yield mock_db

    with patch("database.create_tables", new_callable=AsyncMock), \
         patch("database.engine", MagicMock()):
        from main import app
        from database import get_db
        app.dependency_overrides[get_db] = override_get_db
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/internal/gig-complete", json={"user_id": "provider-1"})
        app.dependency_overrides.clear()

    assert r.status_code == 200
    data = r.json()
    assert data["gigs_completed"] == 10
    assert data["level"] == 2
    assert "Strieborný" in data["level_name"]
