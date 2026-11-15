"""Unit tests for TesseractOCREngine service."""

import numpy as np
import pytest

from app.config import get_settings
from app.services.ocr_engine import TesseractOCREngine


def test_tesseract_engine_initialization():
    """Verifies OCR engine initializes and resolves available languages."""
    settings = get_settings()
    engine = TesseractOCREngine(
        tesseract_cmd=settings.TESSERACT_CMD,
        tessdata_prefix=settings.TESSDATA_PREFIX,
    )
    langs = engine.get_available_languages()
    assert isinstance(langs, list)
    assert len(langs) > 0


def test_tesseract_ocr_execution_on_text():
    """Verifies OCR text recognition and confidence scoring."""
    settings = get_settings()
    engine = TesseractOCREngine(
        tesseract_cmd=settings.TESSERACT_CMD,
        tessdata_prefix=settings.TESSDATA_PREFIX,
    )

    # Create synthetic test image with crisp text
    import cv2
    img = np.ones((120, 600), dtype=np.uint8) * 255
    cv2.putText(img, "HOTEL CHECK IN 2026", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.4, 0, 3)

    result = engine.execute_ocr(img)
    assert "HOTEL" in result.raw_text
    assert "CHECK" in result.raw_text
    assert result.average_confidence > 0.5
    assert len(result.words) >= 3
