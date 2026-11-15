"""KTP Extraction endpoints converting identity card images to hotel check-in records."""

import base64
from pathlib import Path
import re
import time
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import (
    get_hotel_transformer,
    get_ktp_parser,
    get_ocr_engine,
    get_preprocessor,
)
from app.config import Settings, get_settings
from app.core.exceptions import (
    FileSizeExceededError,
    ImageProcessingError,
    InvalidFileTypeError,
)
from app.core.logging import logger
from app.schemas.api_response import Base64ImageRequest
from app.schemas.hotel import HotelCheckInResponse
from app.services.hotel_transformer import HotelCheckInTransformer
from app.services.ktp_parser import KTPParser
from app.services.ocr_engine import TesseractOCREngine
from app.services.preprocessor import ImagePreprocessor

router = APIRouter(prefix="/ktp", tags=["KTP Hotel Check-In"])


def _process_ktp_pipeline(
    image_bytes: bytes,
    preprocessor: ImagePreprocessor,
    ocr_engine: TesseractOCREngine,
    ktp_parser: KTPParser,
    hotel_transformer: HotelCheckInTransformer,
) -> HotelCheckInResponse:
    """Executes the complete decoupled KTP extraction and hotel check-in pipeline."""
    start_time = time.perf_counter()

    # 1. Preprocess image
    _, processed_image = preprocessor.preprocess(image_bytes)

    # 2. Run OCR Engine
    ocr_result = ocr_engine.execute_ocr(processed_image)

    # 3. Parse KTP text
    normalized_ktp = ktp_parser.parse(ocr_result.raw_text)
    raw_fields = ktp_parser._extract_raw_fields(ocr_result.raw_text.splitlines())

    # 4. Transform to Hotel PMS Check-in Profile
    guest_profile, warnings = hotel_transformer.transform(
        ktp_data=normalized_ktp,
        ocr_confidence=ocr_result.average_confidence,
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return HotelCheckInResponse(
        success=True,
        guest_profile=guest_profile,
        nik_detail=normalized_ktp.nik_detail,
        raw_ktp_data=raw_fields,
        ocr_confidence=ocr_result.average_confidence,
        warnings=warnings,
        processing_time_ms=round(elapsed_ms, 2),
    )


@router.post(
    "/extract",
    response_model=HotelCheckInResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract KTP image to Hotel Check-In record (Multipart Upload)",
    description=(
        "Upload a KTP identity card image (JPG, PNG, WebP, etc.). "
        "Applies image preprocessing, Tesseract OCR, regex-based field parsing, "
        "and maps the identity directly into a Hotel Check-In guest record with operational warnings."
    ),
)
async def extract_ktp_from_file(
    file: UploadFile = File(..., description="KTP identity card image file"),
    settings: Settings = Depends(get_settings),
    preprocessor: ImagePreprocessor = Depends(get_preprocessor),
    ocr_engine: TesseractOCREngine = Depends(get_ocr_engine),
    ktp_parser: KTPParser = Depends(get_ktp_parser),
    hotel_transformer: HotelCheckInTransformer = Depends(get_hotel_transformer),
) -> HotelCheckInResponse:
    """Handles multipart file upload for KTP extraction."""
    # 1. Validate file extension
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(
            f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Read bytes and check size
    image_bytes = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise FileSizeExceededError(
            f"Image size exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB ({len(image_bytes)/(1024*1024):.2f}MB provided)."
        )

    if len(image_bytes) == 0:
        raise ImageProcessingError("Empty image file provided.")

    logger.info(f"Processing uploaded KTP: {file.filename} ({len(image_bytes)} bytes)")
    return _process_ktp_pipeline(
        image_bytes=image_bytes,
        preprocessor=preprocessor,
        ocr_engine=ocr_engine,
        ktp_parser=ktp_parser,
        hotel_transformer=hotel_transformer,
    )


@router.post(
    "/extract-base64",
    response_model=HotelCheckInResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract KTP image to Hotel Check-In record (Base64 JSON)",
    description="Accepts a Base64-encoded KTP image and returns the normalized hotel check-in record.",
)
async def extract_ktp_from_base64(
    payload: Base64ImageRequest,
    preprocessor: ImagePreprocessor = Depends(get_preprocessor),
    ocr_engine: TesseractOCREngine = Depends(get_ocr_engine),
    ktp_parser: KTPParser = Depends(get_ktp_parser),
    hotel_transformer: HotelCheckInTransformer = Depends(get_hotel_transformer),
) -> HotelCheckInResponse:
    """Handles base64-encoded image input."""
    raw_b64 = payload.image_base64.strip()

    # Remove data URI prefix if present (e.g. data:image/jpeg;base64,...)
    if "," in raw_b64:
        raw_b64 = raw_b64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(raw_b64)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid base64 payload: {str(e)}",
        )

    if len(image_bytes) == 0:
        raise ImageProcessingError("Decoded base64 payload is empty.")

    logger.info(f"Processing base64 KTP payload ({len(image_bytes)} bytes)")
    return _process_ktp_pipeline(
        image_bytes=image_bytes,
        preprocessor=preprocessor,
        ocr_engine=ocr_engine,
        ktp_parser=ktp_parser,
        hotel_transformer=hotel_transformer,
    )
