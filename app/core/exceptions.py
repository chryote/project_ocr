"""Core custom exceptions for domain and service layers."""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception class for all domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ImageProcessingError(AppException):
    """Raised when an image fails to load, decode, or preprocess."""
    pass


class InvalidFileTypeError(ImageProcessingError):
    """Raised when an uploaded file is not a supported image format."""
    pass


class FileSizeExceededError(ImageProcessingError):
    """Raised when an uploaded file exceeds the allowed size limit."""
    pass


class OCRExecutionError(AppException):
    """Raised when the OCR engine encounters an execution error or timeout."""
    pass


class KTPParsingError(AppException):
    """Raised when extracted text cannot be parsed into KTP data."""
    pass


class NIKValidationError(AppException):
    """Raised when an extracted NIK fails structural validation."""
    pass
