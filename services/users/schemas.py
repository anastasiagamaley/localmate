from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProfileCreate(BaseModel):
    """Called internally by auth service after registration."""
    user_id: str
    email: str
    account_type: str = "regular"


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    city: Optional[str] = None
    service_description: Optional[str] = None
    tags: Optional[str] = None  # comma-separated: "oprava,iPhone,Android"


class ProfilePublic(BaseModel):
    user_id: str
    name: str
    bio: str
    city: str
    service_description: str
    tags: str
    xp: int
    level: int
    gigs_completed: str
    account_type: str
    level_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class GigCompleteRequest(BaseModel):
    """Called by worker after a gig is marked complete."""
    user_id: str     # provider who completed the gig


class XpResponse(BaseModel):
    user_id: str
    xp: int
    level: int
    level_name: str
    gigs_completed: int
    xp_to_next_level: int
