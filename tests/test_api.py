"""Integration tests for FastAPI endpoints."""

import base64
from fastapi import status


def test_health_check_endpoint(client):
    """Verifies GET /api/v1/health returns 200 and tesseract information."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "tesseract_available" in data
    assert data["tesseract_available"] is True


def test_extract_ktp_multipart_upload_success(client, sample_ktp_image_bytes):
    """Verifies POST /api/v1/ktp/extract successfully processes image upload."""
    files = {"file": ("ktp_sample.png", sample_ktp_image_bytes, "image/png")}
    response = client.post("/api/v1/ktp/extract", files=files)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["success"] is True
    assert "guest_profile" in data
    assert "raw_ktp_data" in data
    assert "ocr_confidence" in data
    assert "processing_time_ms" in data

    profile = data["guest_profile"]
    assert profile["identity_type"] == "KTP"
    assert profile["identity_number"] == "3171011505900001"
    assert profile["guest_full_name"] == "Budi Santoso"
    assert profile["is_adult"] is True
    assert profile["registration_card_ready"] is True


def test_extract_ktp_base64_upload_success(client, sample_ktp_image_bytes):
    """Verifies POST /api/v1/ktp/extract-base64 works with JSON payload."""
    b64_str = base64.b64encode(sample_ktp_image_bytes).decode("utf-8")
    payload = {"image_base64": f"data:image/png;base64,{b64_str}"}

    response = client.post("/api/v1/ktp/extract-base64", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["success"] is True
    assert data["guest_profile"]["identity_number"] == "3171011505900001"


def test_extract_ktp_invalid_file_extension(client):
    """Verifies uploading an unsupported extension returns 415."""
    files = {"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    response = client.post("/api/v1/ktp/extract", files=files)
    assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    data = response.json()
    assert data["error_code"] == "INVALID_FILE_TYPE"


def test_extract_ktp_corrupt_image(client):
    """Verifies uploading unreadable file returns 400."""
    files = {"file": ("corrupt.png", b"not-a-valid-png", "image/png")}
    response = client.post("/api/v1/ktp/extract", files=files)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert data["error_code"] == "IMAGE_PROCESSING_FAILED"


def test_root_redirect_to_docs(client):
    """Verifies GET / redirects to Swagger documentation (/docs)."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (status.HTTP_307_TEMPORARY_REDIRECT, status.HTTP_302_FOUND)
    assert response.headers["location"] == "/docs"
