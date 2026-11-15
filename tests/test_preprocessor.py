"""Unit tests for ImagePreprocessor service."""

import io
import cv2
import numpy as np
from PIL import Image
import pytest

from app.core.exceptions import ImageProcessingError
from app.services.preprocessor import ImagePreprocessor


def test_decode_valid_image():
    """Verifies successful decoding of valid image bytes."""
    preprocessor = ImagePreprocessor()
    img = Image.new("RGB", (200, 100), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    decoded = preprocessor.decode_image(buf.getvalue())
    assert isinstance(decoded, np.ndarray)
    assert decoded.shape == (100, 200, 3)


def test_decode_invalid_image_raises_error():
    """Verifies that corrupt or random bytes raise ImageProcessingError."""
    preprocessor = ImagePreprocessor()
    with pytest.raises(ImageProcessingError):
        preprocessor.decode_image(b"not-an-image-data-string")


def test_resize_to_width():
    """Verifies image scaling preserves aspect ratio."""
    preprocessor = ImagePreprocessor()
    original = np.zeros((300, 600, 3), dtype=np.uint8)

    resized = preprocessor.resize_to_width(original, width=1200)
    assert resized.shape[1] == 1200
    assert resized.shape[0] == 600  # 300 * (1200/600) = 600


def test_resize_zero_dimension_raises():
    """Verifies that invalid dimension array raises ImageProcessingError."""
    preprocessor = ImagePreprocessor()
    zero_img = np.zeros((0, 0, 3), dtype=np.uint8)
    with pytest.raises(ImageProcessingError):
        preprocessor.resize_to_width(zero_img, 1200)


def test_deskew_straight_image():
    """Verifies straight image is returned without significant modification."""
    preprocessor = ImagePreprocessor()
    gray = np.zeros((400, 800), dtype=np.uint8)
    cv2.putText(gray, "KTP TEST LINE", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, 2)

    deskewed = preprocessor.deskew(gray)
    assert deskewed.shape == gray.shape


def test_preprocess_pipeline_returns_grayscale_and_binary():
    """Verifies complete preprocessing pipeline outputs expected arrays."""
    preprocessor = ImagePreprocessor(target_width=800)
    img = Image.new("RGB", (400, 250), color=(150, 200, 230))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    denoised, binarized = preprocessor.preprocess(buf.getvalue())
    assert denoised.shape[1] == 800
    assert binarized.shape[1] == 800
    assert len(binarized.shape) == 2  # 2D single channel
    assert np.all((binarized == 0) | (binarized == 255))
