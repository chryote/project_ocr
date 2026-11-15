"""Application Configuration module using Pydantic Settings.

Manages all environment variables and operational defaults with type-safe validation.
"""

from functools import lru_cache
import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the KTP Hotel Check-In OCR API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Information
    APP_NAME: str = "KTP Hotel Check-In OCR API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Standalone POC Backend API for extracting Indonesian KTP (Identity Card) "
        "images into structured Hotel Check-In guest registration records using Tesseract OCR."
    )
    ENV: str = Field(default="development", description="Runtime environment (development, staging, production, test)")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # Server Bindings
    HOST: str = Field(default="0.0.0.0", description="Host address to bind server")
    PORT: int = Field(default=8000, description="Port to bind server")

    # Tesseract OCR Configuration
    TESSERACT_CMD: str = Field(
        default=os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        description="Path to Tesseract executable",
    )
    TESSDATA_PREFIX: str = Field(
        default=str(Path(__file__).resolve().parent.parent / "tessdata"),
        description="Path to tessdata directory containing traineddata files",
    )
    OCR_LANG: str = Field(
        default="ind+eng",
        description="OCR language string. Typically 'ind+eng' or 'ind' or 'eng'",
    )
    OCR_FALLBACK_LANG: str = Field(
        default="eng",
        description="Fallback language string if primary language is unavailable",
    )
    OCR_PSM: int = Field(default=6, description="Tesseract Page Segmentation Mode (PSM)")
    OCR_OEM: int = Field(default=3, description="Tesseract OCR Engine Mode (OEM)")
    OCR_TIMEOUT_SECONDS: int = Field(default=15, description="Timeout for OCR process execution")

    # Image Preprocessing Configuration
    PREPROCESSING_ENABLED: bool = Field(default=True, description="Enable image preprocessing pipeline")
    DESKEW_ENABLED: bool = Field(default=True, description="Enable automatic image deskewing/rotation correction")
    TARGET_DPI_WIDTH: int = Field(default=1200, description="Target pixel width for normalization")
    CLAHE_CLIP_LIMIT: float = Field(default=2.0, description="CLAHE contrast enhancement clip limit")
    CLAHE_GRID_SIZE: int = Field(default=8, description="CLAHE grid tile size")

    # Hotel Business Rules
    MIN_ADULT_AGE: int = Field(default=18, description="Legal minimum adult age for hotel check-in in Indonesia")
    REQUIRE_16_DIGIT_NIK: bool = Field(default=True, description="Strictly enforce 16-digit NIK length")

    # Upload Limitations
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, description="Maximum image upload size in Megabytes")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"],
        description="Allowed image file extensions",
    )

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")


@lru_cache()
def get_settings() -> Settings:
    """Returns cached application settings instance."""
    return Settings()
