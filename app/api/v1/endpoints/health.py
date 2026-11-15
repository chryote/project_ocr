"""Health check and diagnostic endpoints."""

from fastapi import APIRouter, Depends
import pytesseract

from app.api.dependencies import get_ocr_engine
from app.config import Settings, get_settings
from app.core.logging import logger
from app.schemas.api_response import HealthResponse
from app.services.ocr_engine import TesseractOCREngine

router = APIRouter(tags=["Health & System Diagnostics"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API and Tesseract engine health",
    description="Returns service availability, version info, Tesseract binary status, and installed language models.",
)
async def check_health(
    settings: Settings = Depends(get_settings),
    ocr_engine: TesseractOCREngine = Depends(get_ocr_engine),
) -> HealthResponse:
    """Verifies that the API and underlying Tesseract OCR engine are healthy."""
    tesseract_available = False
    tesseract_version = None
    available_langs = []

    try:
        ver = pytesseract.get_tesseract_version()
        tesseract_version = str(ver)
        tesseract_available = True
        available_langs = ocr_engine.get_available_languages()
    except Exception as e:
        logger.error(f"Health check failed to query Tesseract: {e}")
        tesseract_available = False

    return HealthResponse(
        status="healthy" if tesseract_available else "degraded",
        version=settings.APP_VERSION,
        tesseract_available=tesseract_available,
        tesseract_version=tesseract_version,
        available_languages=available_langs,
    )
