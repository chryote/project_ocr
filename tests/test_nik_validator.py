"""Unit tests for NIKValidator service."""

from datetime import date
from app.schemas.ktp import GenderEnum
from app.services.nik_validator import NIKValidator


def test_valid_male_nik():
    """Verifies valid male NIK parsing (day 1-31)."""
    # 31 (DKI Jakarta) 71 (Jakarta Pusat) 01 (Gambir) 15 (Day 15) 05 (May) 90 (1990) 0001
    nik = "3171011505900001"
    res = NIKValidator.validate_and_decode(nik)

    assert res.is_valid_format is True
    assert res.province_code == "31"
    assert res.province_name == "DKI JAKARTA"
    assert res.extracted_gender == GenderEnum.MALE
    assert res.extracted_birth_date == date(1990, 5, 15)
    assert res.sequence_number == "0001"


def test_valid_female_nik_with_plus_40_rule():
    """Verifies female NIK parsing where birth day has +40 added (day 41-71)."""
    # Day 25 + 40 = 65. December (12). Year 1995.
    nik = "3201016512950002"
    res = NIKValidator.validate_and_decode(nik)

    assert res.is_valid_format is True
    assert res.province_code == "32"
    assert res.province_name == "JAWA BARAT"
    assert res.extracted_gender == GenderEnum.FEMALE
    assert res.extracted_birth_date == date(1995, 12, 25)


def test_invalid_length_nik():
    """Verifies rejection of NIKs with fewer or more than 16 digits."""
    short_nik = "3171011505900"
    res = NIKValidator.validate_and_decode(short_nik)
    assert res.is_valid_format is False

    long_nik = "3171011505900001999"
    res = NIKValidator.validate_and_decode(long_nik)
    assert res.is_valid_format is False


def test_invalid_province_or_date():
    """Verifies handling of invalid province code or impossible calendar date."""
    # Province 99 doesn't exist
    res = NIKValidator.validate_and_decode("9971011505900001")
    assert res.is_valid_format is False

    # Month 15 doesn't exist
    res_bad_date = NIKValidator.validate_and_decode("3171011515900001")
    assert res_bad_date.extracted_birth_date is None
    assert res_bad_date.is_valid_format is False
