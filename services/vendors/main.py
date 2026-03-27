"""
Vendors Service — Public REST API for AI agents.
Agents can CREATE / UPDATE / DELETE vendor entries using an API key.
This is intentionally separate from user profiles.
"""
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Boolean, DateTime, Text, select
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Config ──────────────────────────────────────────────────────────────────

class VendorsConfig(BaseSettings):
    database_url: str = "postgresql+asyncpg://localmate:changeme_in_prod@postgres:5432/localmate"
    allowed_origins: str = "http://localhost:3000"
    environment: str = "development"
    vendor_api_key: str = "change_this_vendor_secret_key"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_config() -> VendorsConfig:
    return VendorsConfig()


cfg = get_config()

# ─── DB ──────────────────────────────────────────────────────────────────────

engine = create_async_engine(cfg.database_url, pool_size=10, max_overflow=20, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    tags: Mapped[str] = mapped_column(Text, default="")       # comma-separated
    lat: Mapped[float] = mapped_column(Float, nullable=True)
    lon: Mapped[float] = mapped_column(Float, nullable=True)
    city: Mapped[str] = mapped_column(String(100), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(100), default="agent")   # who added it
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
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


# ─── Auth ────────────────────────────────────────────────────────────────────

api_key_header = APIKeyHeader(name="X-Vendor-API-Key", auto_error=False)


def require_api_key(api_key: str = Security(api_key_header)):
    if api_key != cfg.vendor_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key


# ─── Schemas ──────────────────────────────────────────────────────────────────

class VendorCreate(BaseModel):
    name: str
    description: str = ""
    category: str = ""
    tags: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    city: str = ""
    phone: str = ""
    website: str = ""
    source: str = "agent"


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    active: Optional[bool] = None


class VendorOut(BaseModel):
    id: str
    name: str
    description: str
    category: str
    tags: str
    lat: Optional[float]
    lon: Optional[float]
    city: str
    phone: str
    website: str
    active: bool
    source: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ─── App ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Vendors service ready")
    yield


app = FastAPI(
    title="LocalMate — Vendors API",
    version="0.1.0",
    description="Public API for AI agents to manage vendor database. Requires X-Vendor-API-Key header.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"service": "vendors", "status": "ok"}


@app.post("/", response_model=VendorOut, status_code=201, dependencies=[Depends(require_api_key)])
async def create_vendor(payload: VendorCreate, db: AsyncSession = Depends(get_db)):
    vendor = Vendor(**payload.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    logger.info(f"Vendor created: {vendor.id} — {vendor.name} (source: {vendor.source})")
    return _to_out(vendor)


@app.get("/", response_model=List[VendorOut])
async def list_vendors(
    city: Optional[str] = None,
    category: Optional[str] = None,
    active: bool = True,
    db: AsyncSession = Depends(get_db),
):
    query = select(Vendor).where(Vendor.active == active)
    if city:
        query = query.where(Vendor.city.ilike(f"%{city}%"))
    if category:
        query = query.where(Vendor.category.ilike(f"%{category}%"))
    result = await db.execute(query.limit(100))
    return [_to_out(v) for v in result.scalars().all()]


@app.get("/{vendor_id}", response_model=VendorOut)
async def get_vendor(vendor_id: str, db: AsyncSession = Depends(get_db)):
    vendor = await _get_or_404(vendor_id, db)
    return _to_out(vendor)


@app.patch("/{vendor_id}", response_model=VendorOut, dependencies=[Depends(require_api_key)])
async def update_vendor(vendor_id: str, payload: VendorUpdate, db: AsyncSession = Depends(get_db)):
    vendor = await _get_or_404(vendor_id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(vendor, field, value)
    await db.commit()
    await db.refresh(vendor)
    return _to_out(vendor)


@app.delete("/{vendor_id}", dependencies=[Depends(require_api_key)])
async def delete_vendor(vendor_id: str, db: AsyncSession = Depends(get_db)):
    vendor = await _get_or_404(vendor_id, db)
    vendor.active = False   # soft delete
    await db.commit()
    return {"ok": True, "id": vendor_id}


async def _get_or_404(vendor_id: str, db: AsyncSession) -> Vendor:
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


def _to_out(v: Vendor) -> VendorOut:
    return VendorOut(
        id=v.id, name=v.name, description=v.description, category=v.category,
        tags=v.tags, lat=v.lat, lon=v.lon, city=v.city, phone=v.phone,
        website=v.website, active=v.active, source=v.source,
        created_at=v.created_at.isoformat(), updated_at=v.updated_at.isoformat(),
    )
