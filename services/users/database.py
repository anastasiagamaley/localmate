from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, DateTime, ARRAY, Text
from datetime import datetime, timezone
import uuid

from config import get_config

cfg = get_config()

engine = create_async_engine(
    cfg.database_url,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=cfg.environment == "development",
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    account_type: Mapped[str] = mapped_column(String(20), default="regular")

    # Location
    lat: Mapped[float] = mapped_column(Float, nullable=True)
    lon: Mapped[float] = mapped_column(Float, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    # Service/goods offered
    service_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="")  # comma-separated

    # Gamification
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    gigs_completed: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
