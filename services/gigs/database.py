from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, Text, Float, Boolean
from datetime import datetime, timezone
import enum
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

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class GigStatus(str, enum.Enum):
    pending   = "pending"     # создан клиентом, ждёт провайдера
    accepted  = "accepted"    # провайдер принял
    completed = "completed"   # клиент подтвердил выполнение
    cancelled = "cancelled"   # отменён
    disputed  = "disputed"    # спор (на будущее)
    flagged   = "flagged"     # подозрительная цена — заморожен


class Gig(Base):
    __tablename__ = "gigs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Участники
    client_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    provider_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Детали
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")

    # Цена
    price_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    recommended_min: Mapped[int] = mapped_column(Integer, default=0)   # от AI
    recommended_max: Mapped[int] = mapped_column(Integer, default=0)   # от AI

    # Статус
    status: Mapped[GigStatus] = mapped_column(
        SAEnum(GigStatus), default=GigStatus.pending, nullable=False, index=True
    )

    # Флаги безопасности
    price_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_reason: Mapped[str] = mapped_column(String(255), default="")

    # Локации (на момент создания)
    client_lat: Mapped[float] = mapped_column(Float, nullable=True)
    client_lon: Mapped[float] = mapped_column(Float, nullable=True)

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
