"""Pytest fixtures and test configuration."""

import io
from typing import Generator
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image
import pytest

from app.main import create_app
from benchmarks.mock_generator import SyntheticKTPConfig, SyntheticKTPGenerator


@pytest.fixture(scope="session")
def app_instance():
    """Initializes a FastAPI test application instance."""
    return create_app()


@pytest.fixture(scope="session")
def client(app_instance) -> Generator[TestClient, None, None]:
    """Provides a TestClient for testing HTTP endpoints."""
    with TestClient(app_instance) as c:
        yield c


@pytest.fixture
def sample_ktp_image_bytes() -> bytes:
    """Returns image bytes for a standard male adult synthetic KTP."""
    cfg = SyntheticKTPConfig(
        nik="3171011505900001",
        nama="BUDI SANTOSO",
        tempat_lahir="JAKARTA",
        tanggal_lahir="15-05-1990",
        jenis_kelamin="LAKI-LAKI",
        golongan_darah="O",
        alamat="JL. MH THAMRIN NO. 28",
        rt_rw="005/002",
        kel_desa="GONDANGDIA",
        kecamatan="MENTENG",
    )
    return SyntheticKTPGenerator.generate_image_bytes(cfg)


@pytest.fixture
def female_minor_ktp_bytes() -> bytes:
    """Returns image bytes for a female minor (16yo) synthetic KTP."""
    # Day 20 + 40 = 60 for female, month 08, year 10 (2010)
    cfg = SyntheticKTPConfig(
        nik="3271016008100002",
        nama="ANNISA PUTRI",
        tempat_lahir="BOGOR",
        tanggal_lahir="20-08-2010",
        jenis_kelamin="PEREMPUAN",
        golongan_darah="A",
        alamat="JL. PAJAJARAN NO. 10",
        rt_rw="002/003",
        kel_desa="BARANANGSIANG",
        kecamatan="BOGOR TIMUR",
        provinsi="PROVINSI JAWA BARAT",
        kota="KOTA BOGOR",
    )
    return SyntheticKTPGenerator.generate_image_bytes(cfg)


@pytest.fixture
def sample_raw_ktp_text() -> str:
    """Sample realistic OCR raw text representation."""
    return (
        "PROVINSI DKI JAKARTA\n"
        "KOTA JAKARTA SELATAN\n"
        "NIK : 3174051010880003\n"
        "Nama : RYAN KURNIAWAN\n"
        "Tempat/Tgl Lahir : JAKARTA, 10-10-1988\n"
        "Jenis Kelamin : LAKI-LAKI Gol. Darah : B\n"
        "Alamat : JL. FATMAWATI RAYA NO. 15\n"
        "RT/RW : 004/007\n"
        "Kel/Desa : CILANDAK BARAT\n"
        "Kecamatan : CILANDAK\n"
        "Agama : ISLAM\n"
        "Status Perkawinan : KAWIN\n"
        "Pekerjaan : WIRASWASTA\n"
        "Kewarganegaraan : WNI\n"
        "Berlaku Hingga : SEUMUR HIDUP\n"
    )
