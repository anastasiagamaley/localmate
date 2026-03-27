from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum
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
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class TxType(str, enum.Enum):
    welcome   = "welcome"       # registration bonus
    contact   = "contact"       # open someone's contact
    payment   = "payment"       # pay for a service
    purchase  = "purchase"      # buy tokens with €
    withdrawal = "withdrawal"   # withdraw to bank (ICO only)
    refund    = "refund"


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)  # stored as integer (tokens)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    counterpart_id: Mapped[str] = mapped_column(String(36), nullable=True)  # other user
    amount: Mapped[int] = mapped_column(Integer, nullable=False)   # positive = credit, negative = debit
    tx_type: Mapped[TxType] = mapped_column(SAEnum(TxType), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
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
