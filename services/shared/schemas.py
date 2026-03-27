from pydantic import BaseModel
from typing import Any, Optional


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    service: str
    status: str = "ok"
    version: str = "0.1.0"
