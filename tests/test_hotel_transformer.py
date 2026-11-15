"""Unit tests for HotelCheckInTransformer service."""

from datetime import date
from app.schemas.hotel import WarningSeverity
from app.schemas.ktp import AddressDetail, GenderEnum, KTPNormalized
from app.services.hotel_transformer import HotelCheckInTransformer
from app.services.nik_validator import NIKValidator


def test_transform_adult_guest_profile():
    """Verifies adult guest profile generation and address formatting."""
    nik = "3171011505900001"
    detail = NIKValidator.validate_and_decode(nik)
    ktp = KTPNormalized(
        nik=nik,
        nama="BUDI SANTOSO",
        tempat_lahir="JAKARTA",
        tanggal_lahir=date(1990, 5, 15),
        jenis_kelamin=GenderEnum.MALE,
        alamat=AddressDetail(
            street="JL. MH THAMRIN NO. 28",
            rt="005",
            rw="002",
            kel_desa="GONDANGDIA",
            kecamatan="MENTENG",
            city="JAKARTA PUSAT",
            province="DKI JAKARTA",
        ),
        pekerjaan="KARYAWAN SWASTA",
        status_perkawinan="KAWIN",
        kewarganegaraan="WNI",
        nik_detail=detail,
    )

    transformer = HotelCheckInTransformer(min_adult_age=18)
    profile, warnings = transformer.transform(ktp, ocr_confidence=0.92)

    assert profile.guest_full_name == "Budi Santoso"
    assert profile.identity_type == "KTP"
    assert profile.identity_number == "3171011505900001"
    assert profile.is_adult is True
    assert profile.age >= 18
    assert profile.nationality == "INDONESIA"
    assert profile.nationality_code == "ID"
    assert "JL. MH THAMRIN NO. 28" in profile.full_residential_address
    assert profile.registration_card_ready is True
    assert len(warnings) == 0


def test_minor_guest_triggers_warning():
    """Verifies minor guest (<18) triggers MINOR_GUEST warning."""
    # 15 years old
    birth_date = date.today().replace(year=date.today().year - 15)
    ktp = KTPNormalized(
        nik="3171011505110001",
        nama="REHAN JUNIOR",
        tanggal_lahir=birth_date,
        jenis_kelamin=GenderEnum.MALE,
        alamat=AddressDetail(street="JL. ANGGREK NO. 2"),
    )

    transformer = HotelCheckInTransformer(min_adult_age=18)
    profile, warnings = transformer.transform(ktp)

    assert profile.is_adult is False
    warning_codes = [w.code for w in warnings]
    assert "MINOR_GUEST" in warning_codes


def test_nik_cross_validation_mismatch():
    """Verifies mismatch between printed card fields and NIK encoded fields produces warnings."""
    # Encoded birth date: 15-05-1990, Male
    nik = "3171011505900001"
    detail = NIKValidator.validate_and_decode(nik)

    # Printed date says 20-08-1992, printed gender says FEMALE
    ktp = KTPNormalized(
        nik=nik,
        nama="BUDI SANTOSO",
        tanggal_lahir=date(1992, 8, 20),
        jenis_kelamin=GenderEnum.FEMALE,
        alamat=AddressDetail(street="JL. MERDEKA"),
        nik_detail=detail,
    )

    transformer = HotelCheckInTransformer()
    _, warnings = transformer.transform(ktp)

    codes = [w.code for w in warnings]
    assert "NIK_DOB_MISMATCH" in codes
    assert "NIK_GENDER_MISMATCH" in codes


def test_low_ocr_confidence_warning():
    """Verifies low OCR confidence generates appropriate front-desk alert."""
    ktp = KTPNormalized(
        nik="3171011505900001",
        nama="BUDI SANTOSO",
        tanggal_lahir=date(1990, 5, 15),
        jenis_kelamin=GenderEnum.MALE,
        alamat=AddressDetail(street="JL. MERDEKA"),
    )
    transformer = HotelCheckInTransformer()
    _, warnings = transformer.transform(ktp, ocr_confidence=0.55)

    codes = [w.code for w in warnings]
    assert "LOW_OCR_CONFIDENCE" in codes
