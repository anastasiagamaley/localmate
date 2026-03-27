from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from database import GigStatus


class PriceCheckRequest(BaseModel):
    """Client asks AI: is this price reasonable for this service?"""
    title: str
    description: str = ""
    proposed_price: int


class PriceCheckResponse(BaseModel):
    proposed_price: int
    recommended_min: int
    recommended_max: int
    is_reasonable: bool
    warning: Optional[str] = None       # показываем если цена подозрительная
    ai_explanation: str


class GigCreate(BaseModel):
    provider_id: str
    title: str
    description: str = ""
    category: str = ""
    price_tokens: int
    recommended_min: int = 0
    recommended_max: int = 0
    client_lat: Optional[float] = None
    client_lon: Optional[float] = None

    @field_validator("price_tokens")
    @classmethod
    def price_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Cena musí byť väčšia ako 0")
        return v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Názov nesmie byť prázdny")
        return v.strip()


class GigOut(BaseModel):
    id: str
    client_id: str
    provider_id: str
    title: str
    description: str
    category: str
    price_tokens: int
    recommended_min: int
    recommended_max: int
    status: str
    price_flagged: bool
    flag_reason: str
    client_lat: Optional[float]
    client_lon: Optional[float]
    created_at: datetime
    accepted_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    class Config:
        from_attributes = True


class GigSummary(BaseModel):
    """Compact version for lists."""
    id: str
    title: str
    price_tokens: int
    status: str
    price_flagged: bool
    client_id: str
    provider_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class CancelRequest(BaseModel):
    reason: str = ""
