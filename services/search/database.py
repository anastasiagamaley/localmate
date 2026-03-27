"""
Search service shares the profiles table with users service.
In a full microservices setup this would be an internal API call,
but for MVP we share the same Postgres DB for simplicity.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, DateTime, Text
from datetime import datetime, timezone

from config import get_config

cfg = get_config()

engine = create_async_engine(cfg.database_url, pool_size=10, max_overflow=20, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Profile(Base):
    """Mirror of users service Profile — read-only in search service."""
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    service_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="")
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    lat: Mapped[float] = mapped_column(Float, nullable=True)
    lon: Mapped[float] = mapped_column(Float, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=1)
    gigs_completed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    pass  # Tables created by users service — search only reads
