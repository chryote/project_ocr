"""Application Configuration module using Pydantic Settings.

Manages all environment variables and operational defaults with type-safe validation.
"""

from functools import lru_cache
import os
from pathlib import Path
import shutil
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_default_tesseract_cmd() -> str:
    """Detects default Tesseract binary across Windows, Linux, macOS, and Docker containers."""
    if "TESSERACT_CMD" in os.environ and os.environ["TESSERACT_CMD"].strip():
        return os.environ["TESSERACT_CMD"].strip()

    # 1. Check system PATH (standard in Docker, Linux, and macOS Homebrew)
    which_cmd = shutil.which("tesseract")
    if which_cmd:
        return which_cmd

    # 2. Check standard Homebrew macOS paths
    for mac_path in ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"):
        if os.path.isfile(mac_path):
            return mac_path

    # 3. Check standard Linux path
    if os.path.isfile("/usr/bin/tesseract"):
        return "/usr/bin/tesseract"

    # 4. Check standard Windows default path
    win_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.isfile(win_default):
        return win_default

    return "tesseract"


def get_default_tessdata_prefix() -> str:
    """Detects default tessdata directory across project directory and system paths."""
    if "TESSDATA_PREFIX" in os.environ and os.environ["TESSDATA_PREFIX"].strip():
        return os.environ["TESSDATA_PREFIX"].strip()

    # Repository / application bundled tessdata
    local_dir = Path(__file__).resolve().parent.parent / "tessdata"
    if local_dir.is_dir():
        return str(local_dir)

    # Standard system tessdata directories (Debian/Ubuntu, Homebrew macOS)
    for sys_dir in (
        "/usr/share/tesseract-ocr/5/tessdata",
        "/usr/share/tesseract-ocr/4.00/tessdata",
        "/usr/share/tessdata",
        "/opt/homebrew/share/tessdata",
        "/usr/local/share/tessdata",
    ):
        if os.path.isdir(sys_dir):
            return sys_dir

    return str(local_dir)


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
        default_factory=get_default_tesseract_cmd,
        description="Path to Tesseract executable",
    )
    TESSDATA_PREFIX: str = Field(
        default_factory=get_default_tessdata_prefix,
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
