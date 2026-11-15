# KTP Hotel Check-In OCR API

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=flat-square)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-91%25-brightgreen.svg?style=flat-square)](https://pytest.org/)

A standalone, proof-of-concept backend Python API using Tesseract OCR to extract Indonesian National Identity Cards (KTP) into structured Hotel Property Management System (PMS) guest check-in profiles.

Built with strict separation of concerns, zero god classes, comprehensive unit testing, and sustainable engineering practices.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [API](#api)
- [Benchmarks](#benchmarks)
- [Contributing](#contributing)
- [License](#license)

## Background

Front-desk operations in Indonesian hotels require collecting accurate guest identification data during check-in to satisfy regulatory reporting, billing folios, and guest ledger registration. Manual data entry from physical KTP cards is time-consuming, prone to human typographical errors, and creates friction for guests in hotel lobbies.

Extracting data from Indonesian KTPs poses several domain-specific engineering challenges:
1. **Low Lighting & Glare:** Photos taken at reception desks often exhibit skewed angles, uneven contrast, or reflection glare.
2. **Statutory Identity Semantics (NIK):** The 16-digit Indonesian National Identity Number (*Nomor Induk Kependudukan* - NIK) encodes province codes, city codes, and statutory female birth date rules (the statutory addition of 40 to the birth day for females).
3. **Hotel Operational Rules:** Receptionists need immediate actionable warnings, such as detecting minor guests (under 18 years of age), flag mismatches between printed text and decoded NIK digits, and verify residency addresses.

This project delivers a modular, standalone API that addresses these challenges through a decoupled pipeline:
- **Image Preprocessing:** Contrast Limited Adaptive Histogram Equalization (CLAHE), bilateral denoising, contour-based deskewing, and Otsu binarization.
- **Tesseract OCR Engine:** Tesseract 5 integration configured with LSTM models (`ind+eng`), custom Page Segmentation Modes (PSM), and word-level confidence evaluation.
- **Text Normalization & Parsing:** Heuristic cleaning routines resolving common OCR substitutions, followed by regular expression field extraction.
- **NIK Demographic Decoder:** Validates 16-digit integrity, decodes administrative region codes, and handles the statutory female `+40` day rule.
- **Hotel PMS Transformer:** Maps extracted data into normalized guest profiles, evaluates legal adult check-in age, compiles registration addresses, and flags front-desk alerts.

## Install

### Prerequisites

- **Python:** Version 3.10 or higher.
- **Tesseract OCR:** Tesseract binary version 5.x installed on the host system.
  - Windows: UB-Mannheim Tesseract installer (e.g., `winget install UB-Mannheim.TesseractOCR` or download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)).
  - Linux (Ubuntu/Debian): `sudo apt-get install tesseract-ocr tesseract-ocr-ind libtesseract-dev`
  - macOS: `brew install tesseract tesseract-lang`

### Setup

1. Clone or navigate to the repository directory:
   ```bash
   cd d:/project_ocr
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env` and adjust the paths to your local Tesseract executable and tessdata directory if necessary:
   ```bash
   cp .env.example .env
   ```

   *Windows default path in `.env`:*
   ```ini
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   TESSDATA_PREFIX=./tessdata
   OCR_LANG=ind+eng
   ```

## Usage

### Running the API Server

Start the standalone FastAPI server using the entrypoint module:

```bash
python -m app.main
```

Alternatively, start with Uvicorn live reload during development:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The service will bind to `http://localhost:8000`.

### Accessing Interactive Documentation

- **Swagger UI:** Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.
- **ReDoc:** Open [http://localhost:8000/redoc](http://localhost:8000/redoc).

### Running Unit Tests

The test suite contains 29 comprehensive test cases covering every service, validation rule, error handler, and API endpoint with 91% code coverage:

```bash
pytest
```

To run with full coverage breakdown:

```bash
pytest --cov=app --cov-report=term-missing
```

### Running Performance Benchmarks

An automated benchmark suite evaluates end-to-end processing latency, throughput, memory consumption, and field extraction accuracy across clean, skewed, noisy, female (+40 rule), and minor guest scenarios:

```bash
python -m benchmarks.benchmark_suite --iterations 3 --output benchmarks/benchmark_results.json
```

## API

Comprehensive API documentation is available in [docs/api_documentation.md](docs/api_documentation.md).

### Quick Endpoint Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health, Tesseract version, and language models |
| `POST` | `/api/v1/ktp/extract` | Upload KTP image file (`multipart/form-data`) |
| `POST` | `/api/v1/ktp/extract-base64` | Send Base64 image payload (`application/json`) |

### Example Request

Extract KTP using cURL:

```bash
curl -X POST "http://localhost:8000/api/v1/ktp/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ktp_sample.png;type=image/png"
```

### Example Response

```json
{
  "success": true,
  "guest_profile": {
    "guest_full_name": "Budi Santoso",
    "identity_type": "KTP",
    "identity_number": "3171011505900001",
    "gender": "MALE",
    "date_of_birth": "1990-05-15",
    "place_of_birth": "Jakarta",
    "age": 36,
    "is_adult": true,
    "nationality_code": "ID",
    "nationality": "INDONESIA",
    "full_residential_address": "JL. MH THAMRIN NO. 28, RT 005 / RW 002, Kel. GONDANGDIA, Kec. MENTENG, KOTA/KABUPATEN JAKARTA PUSAT, PROVINSI DKI JAKARTA",
    "occupation": "Karyawan Swasta",
    "marital_status": "Kawin",
    "registration_card_ready": true
  },
  "nik_detail": {
    "nik": "3171011505900001",
    "is_valid_format": true,
    "province_code": "31",
    "province_name": "DKI JAKARTA",
    "city_code": "71",
    "district_code": "01",
    "extracted_birth_date": "1990-05-15",
    "extracted_gender": "MALE",
    "sequence_number": "0001"
  },
  "raw_ktp_data": {
    "provinsi": "PROVINSI DKI JAKARTA",
    "kota_kabupaten": "KOTA/KABUPATEN JAKARTA PUSAT",
    "nik": "3171011505900001",
    "nama": "BUDI SANTOSO",
    "tempat_lahir": "JAKARTA",
    "tanggal_lahir": "15-05-1990",
    "jenis_kelamin": "LAKI-LAKI",
    "golongan_darah": "O",
    "alamat": "JL. MH THAMRIN NO. 28",
    "rt_rw": "005/002",
    "kel_desa": "GONDANGDIA",
    "kecamatan": "MENTENG",
    "agama": "ISLAM",
    "status_perkawinan": "KAWIN",
    "pekerjaan": "KARYAWAN SWASTA",
    "kewarganegaraan": "WNI",
    "berlaku_hingga": "SEUMUR HIDUP"
  },
  "ocr_confidence": 0.8736,
  "warnings": [],
  "processing_time_ms": 339.96
}
```

### Operational Check-In Warning Codes

The API automatically flags data discrepancies for front-desk receptionists:

| Code | Severity | Meaning |
|---|---|---|
| `MINOR_GUEST` | `WARNING` | Guest is under 18 years old. Adult accompaniment required. |
| `INVALID_NIK_LENGTH` | `CRITICAL` | Extracted NIK is not 16 digits. Re-scan required. |
| `NIK_DOB_MISMATCH` | `WARNING` | Printed birth date does not match encoded NIK birth date. |
| `NIK_GENDER_MISMATCH` | `WARNING` | Printed gender does not match NIK female `+40` encoded gender. |
| `LOW_OCR_CONFIDENCE` | `WARNING` | Mean OCR confidence < 65%. Manual review recommended. |
| `INCOMPLETE_ADDRESS` | `INFO` | Street name not detected. Front desk verification needed. |

## Benchmarks

Benchmarked on single-core CPU execution across 10 diverse synthetic KTP scenarios (clean, skewed, noisy, female, minor):

| Metric | Measured Value |
|---|---|
| **Mean End-to-End Latency** | 339.96 ms |
| **Median Latency ($p_{50}$)** | 341.75 ms |
| **95th Percentile ($p_{95}$)** | 369.46 ms |
| **99th Percentile ($p_{99}$)** | 369.46 ms |
| **Throughput** | 2.94 requests / second |
| **Memory Delta (RSS)** | 9.07 MB |
| **NIK Extraction Accuracy** | 100.0% |
| **Name Extraction Accuracy** | 100.0% |
| **Gender Extraction Accuracy** | 100.0% |
| **Mean OCR Confidence** | 87.36% |

### Component Latency Breakdown

```
Image Preprocessing (CLAHE, Deskew, Resize) :  17.96 ms  ( 5.3%)
Tesseract OCR Engine Execution              : 320.37 ms  (94.2%)
KTP Field Regex Parsing                     :   1.52 ms  ( 0.4%)
Hotel Check-In Transformation & Validation  :   0.11 ms  ( 0.1%)
----------------------------------------------------------------
Total Average Latency                       : 339.96 ms  (100.0%)
```

## Contributing

PRs accepted. Please review the following guidelines before submitting code:

1. Follow PEP 8 style guides and type annotations.
2. Ensure no god classes or functions are introduced; maintain single-responsibility modules in `app/services/`.
3. Add unit tests for new functionality in `tests/`.
4. Verify all tests pass with `pytest` and coverage remains above 90%.
5. Run the benchmark suite to ensure no performance regressions.

## License

[MIT](LICENSE) © 2026 chryote
