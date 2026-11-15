"""Schemas module exporting all API and domain data transfer objects."""

from app.schemas.ktp import (
    AddressDetail,
    GenderEnum,
    KTPNormalized,
    NIKDetail,
    RawKTPFields,
)
from app.schemas.hotel import (
    CheckInWarning,
    HotelCheckInResponse,
    HotelGuestProfile,
    WarningSeverity,
)
from app.schemas.api_response import (
    Base64ImageRequest,
    ErrorResponse,
    HealthResponse,
)

__all__ = [
    "AddressDetail",
    "GenderEnum",
    "KTPNormalized",
    "NIKDetail",
    "RawKTPFields",
    "CheckInWarning",
    "HotelCheckInResponse",
    "HotelGuestProfile",
    "WarningSeverity",
    "Base64ImageRequest",
    "ErrorResponse",
    "HealthResponse",
]
