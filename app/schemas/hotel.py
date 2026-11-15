"""Pydantic schemas for Hotel Check-In guest registration records."""

from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.ktp import GenderEnum, RawKTPFields, NIKDetail


class WarningSeverity(str, Enum):
    """Severity levels for hotel check-in operational warnings."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class CheckInWarning(BaseModel):
    """Operational flag or warning for front-desk receptionists."""
    code: str = Field(..., description="Machine-readable code, e.g. MINOR_GUEST, NIK_MISMATCH")
    message: str = Field(..., description="Human-readable warning explanation")
    severity: WarningSeverity = Field(..., description="Severity level")


class HotelGuestProfile(BaseModel):
    """Normalized Guest Profile formatted for Hotel PMS (Property Management System)."""
    guest_full_name: str = Field(..., description="Full legal name of the hotel guest")
    identity_type: str = Field(default="KTP", description="Identity document type")
    identity_number: str = Field(..., description="KTP NIK number")
    gender: GenderEnum = Field(..., description="Guest gender (MALE / FEMALE / UNKNOWN)")
    date_of_birth: Optional[date] = Field(None, description="Guest birth date (ISO format YYYY-MM-DD)")
    place_of_birth: Optional[str] = Field(None, description="Place of birth")
    age: Optional[int] = Field(None, description="Calculated guest age in years")
    is_adult: bool = Field(..., description="Whether guest is 18 years or older")
    nationality_code: str = Field(default="ID", description="ISO 3166-1 alpha-2 country code")
    nationality: str = Field(default="INDONESIA", description="Full country name")
    full_residential_address: str = Field(..., description="Compiled single-string address for registration card")
    occupation: Optional[str] = Field(None, description="Guest occupation")
    marital_status: Optional[str] = Field(None, description="Marital status")
    registration_card_ready: bool = Field(
        ...,
        description="Indicates whether guest profile has minimum required fields for instant check-in",
    )


class HotelCheckInResponse(BaseModel):
    """Complete API response for KTP-to-Hotel check-in extraction."""
    success: bool = Field(default=True, description="Extraction success status")
    guest_profile: HotelGuestProfile = Field(..., description="Extracted hotel guest profile")
    nik_detail: Optional[NIKDetail] = Field(None, description="Decoded NIK demographics")
    raw_ktp_data: RawKTPFields = Field(..., description="Raw text parsed from OCR")
    ocr_confidence: float = Field(..., description="Overall OCR confidence score between 0.0 and 1.0")
    warnings: List[CheckInWarning] = Field(default_factory=list, description="List of operational check-in warnings")
    processing_time_ms: float = Field(..., description="End-to-end processing latency in milliseconds")
