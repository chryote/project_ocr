"""Unit tests for KTPParser service."""

from datetime import date
from app.schemas.ktp import GenderEnum
from app.services.ktp_parser import KTPParser


def test_parse_sample_raw_ktp_text(sample_raw_ktp_text):
    """Verifies complete parsing of realistic KTP OCR text."""
    parser = KTPParser()
    ktp = parser.parse(sample_raw_ktp_text)

    assert ktp.nik == "3174051010880003"
    assert ktp.nama == "RYAN KURNIAWAN"
    assert ktp.tempat_lahir == "JAKARTA"
    assert ktp.tanggal_lahir == date(1988, 10, 10)
    assert ktp.jenis_kelamin == GenderEnum.MALE
    assert ktp.golongan_darah == "B"
    assert ktp.alamat.street == "JL. FATMAWATI RAYA NO. 15"
    assert ktp.alamat.rt == "004"
    assert ktp.alamat.rw == "007"
    assert ktp.alamat.kel_desa == "CILANDAK BARAT"
    assert ktp.alamat.kecamatan == "CILANDAK"
    assert ktp.agama == "ISLAM"
    assert ktp.status_perkawinan == "KAWIN"
    assert ktp.pekerjaan == "WIRASWASTA"
    assert ktp.kewarganegaraan == "WNI"


def test_fallback_to_nik_when_birthdate_or_gender_missing_in_text():
    """Verifies that missing printed birth date or gender falls back to NIK decoding."""
    parser = KTPParser()
    # Female born 25-12-1995 (day 65)
    text = (
        "NIK : 3201016512950002\n"
        "Nama : SITI AMINAH\n"
        "Alamat : JL. MERDEKA NO. 1\n"
    )
    ktp = parser.parse(text)
    assert ktp.nik == "3201016512950002"
    assert ktp.nama == "SITI AMINAH"
    assert ktp.tanggal_lahir == date(1995, 12, 25)
    assert ktp.jenis_kelamin == GenderEnum.FEMALE
