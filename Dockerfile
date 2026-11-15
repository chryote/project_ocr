# ==============================================================================
# Multi-Platform Dockerfile for KTP Hotel Check-In OCR API
# Supported architectures: linux/amd64 (Windows x86_64, Linux, Intel Mac),
#                          linux/arm64 (macOS Apple Silicon M1/M2/M3/M4, Linux ARM64)
# ==============================================================================

FROM python:3.11-slim-bookworm

# Configure Python execution and default OCR paths
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TESSERACT_CMD=/usr/bin/tesseract \
    TESSDATA_PREFIX=/app/tessdata \
    HOST=0.0.0.0 \
    PORT=8000

# Install system dependencies:
# - Tesseract OCR engine v5 and language models (Indonesian, English, OSD)
# - OpenCV runtime libraries (libgl1, libglib2.0-0)
# - curl for container health check probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ind \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set standard working directory
WORKDIR /app

# Create a non-privileged user and group for security compliance
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Install Python dependencies in a separate layer for build cache reuse
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code, models, tests, benchmarks, and configuration
COPY app/ ./app/
COPY tessdata/ ./tessdata/
COPY tests/ ./tests/
COPY benchmarks/ ./benchmarks/
COPY pytest.ini .

# Set appropriate permissions for the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root application user
USER appuser

# Expose FastAPI HTTP server port
EXPOSE 8000

# Container health check using the API's native /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command to run the production FastAPI application via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
