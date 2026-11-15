"""Dependency Injection provider for FastAPI routes.

Initializes and caches singleton or request-scoped services.
"""

from functools import lru_cache
from app.config import Settings, get_settings
from app.services.hotel_transformer import HotelCheckInTransformer
from app.services.ktp_parser import KTPParser
from app.services.nik_validator import NIKValidator
from app.services.ocr_engine import TesseractOCREngine
from app.services.preprocessor import ImagePreprocessor


@lru_cache()
def get_preprocessor() -> ImagePreprocessor:
    """Provides cached ImagePreprocessor instance."""
    settings = get_settings()
    return ImagePreprocessor(
        target_width=settings.TARGET_DPI_WIDTH,
        deskew=settings.DESKEW_ENABLED,
        clahe_clip_limit=settings.CLAHE_CLIP_LIMIT,
        clahe_grid_size=settings.CLAHE_GRID_SIZE,
    )


@lru_cache()
def get_ocr_engine() -> TesseractOCREngine:
    """Provides cached TesseractOCREngine instance."""
    settings = get_settings()
    return TesseractOCREngine(
        tesseract_cmd=settings.TESSERACT_CMD,
        tessdata_prefix=settings.TESSDATA_PREFIX,
        default_lang=settings.OCR_LANG,
        fallback_lang=settings.OCR_FALLBACK_LANG,
        psm=settings.OCR_PSM,
        oem=settings.OCR_OEM,
        timeout=settings.OCR_TIMEOUT_SECONDS,
    )


@lru_cache()
def get_nik_validator() -> NIKValidator:
    """Provides cached NIKValidator instance."""
    return NIKValidator()


@lru_cache()
def get_ktp_parser() -> KTPParser:
    """Provides cached KTPParser instance with injected NIKValidator."""
    return KTPParser(nik_validator=get_nik_validator())


@lru_cache()
def get_hotel_transformer() -> HotelCheckInTransformer:
    """Provides cached HotelCheckInTransformer instance."""
    settings = get_settings()
    return HotelCheckInTransformer(min_adult_age=settings.MIN_ADULT_AGE)
