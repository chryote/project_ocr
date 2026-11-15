"""API request and standard response schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Base64ImageRequest(BaseModel):
    """Payload schema for base64-encoded image input."""
    image_base64: str = Field(
        ...,
        description="Base64 encoded string of the KTP image (supports raw base64 or data URI scheme)",
    )


class HealthResponse(BaseModel):
    """Health check status response."""
    status: str = Field(default="healthy", description="Application operational status")
    version: str = Field(..., description="Application version")
    tesseract_available: bool = Field(..., description="Whether Tesseract binary is accessible")
    tesseract_version: Optional[str] = Field(None, description="Installed Tesseract OCR version")
    available_languages: list[str] = Field(default_factory=list, description="Installed Tesseract languages")


class ErrorResponse(BaseModel):
    """Standardized error response payload."""
    success: bool = Field(default=False)
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="User-facing error description")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed diagnostic context")
