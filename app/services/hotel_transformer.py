"""Hotel Check-In Transformation Service.

Maps normalized KTP identity records into hotel PMS (Property Management System)
guest profiles, performs age/adult checks, formats addresses for registration folios,
and generates front-desk operational alerts.
"""

from datetime import date
from typing import List, Optional
from app.schemas.hotel import (
    CheckInWarning,
    HotelGuestProfile,
    WarningSeverity,
)
from app.schemas.ktp import AddressDetail, GenderEnum, KTPNormalized


class HotelCheckInTransformer:
    """Transforms normalized KTP records into hotel check-in guest profiles."""

    def __init__(self, min_adult_age: int = 18):
        self.min_adult_age = min_adult_age

    def transform(
        self,
        ktp_data: KTPNormalized,
        ocr_confidence: float = 1.0,
    ) -> tuple[HotelGuestProfile, List[CheckInWarning]]:
        """Transforms KTP data into a HotelGuestProfile along with front-office warnings."""
        warnings: List[CheckInWarning] = []

        # 1. Calculate Age & Adult Status
        age = self._calculate_age(ktp_data.tanggal_lahir)
        is_adult = age >= self.min_adult_age if age is not None else False

        if age is not None and not is_adult:
            warnings.append(
                CheckInWarning(
                    code="MINOR_GUEST",
                    message=(
                        f"Guest is {age} years old (under {self.min_adult_age}). "
                        "Hotel policy requires adult accompaniment or parental consent."
                    ),
                    severity=WarningSeverity.WARNING,
                )
            )
        elif age is None:
            warnings.append(
                CheckInWarning(
                    code="UNKNOWN_AGE",
                    message="Birth date is missing or unparseable. Age could not be verified.",
                    severity=WarningSeverity.INFO,
                )
            )

        # 2. Cross-validate NIK consistency
        self._cross_validate_nik(ktp_data, warnings)

        # 3. Check OCR Confidence
        if ocr_confidence < 0.65:
            warnings.append(
                CheckInWarning(
                    code="LOW_OCR_CONFIDENCE",
                    message=f"Low OCR confidence ({ocr_confidence * 100:.1f}%). Please manually inspect document.",
                    severity=WarningSeverity.WARNING,
                )
            )

        # 4. Format Residential Address
        full_address = self._format_address(ktp_data.alamat)
        has_valid_address = bool(ktp_data.alamat.street and full_address != "Address Not Provided")
        if not ktp_data.alamat.street:
            warnings.append(
                CheckInWarning(
                    code="INCOMPLETE_ADDRESS",
                    message="Street address was not detected. Manual entry may be required.",
                    severity=WarningSeverity.INFO,
                )
            )

        # 5. Nationality Resolution
        is_indonesian = ktp_data.kewarganegaraan.upper() == "WNI"
        nationality_code = "ID" if is_indonesian else "FOREIGN"
        nationality_name = "INDONESIA" if is_indonesian else ktp_data.kewarganegaraan

        # 6. Readiness for Check-In
        ready_for_checkin = bool(
            ktp_data.nama
            and ktp_data.nama != "UNKNOWN GUEST"
            and len(ktp_data.nik) == 16
            and ktp_data.jenis_kelamin != GenderEnum.UNKNOWN
            and has_valid_address
        )

        profile = HotelGuestProfile(
            guest_full_name=ktp_data.nama.title(),
            identity_type="KTP",
            identity_number=ktp_data.nik,
            gender=ktp_data.jenis_kelamin,
            date_of_birth=ktp_data.tanggal_lahir,
            place_of_birth=ktp_data.tempat_lahir.title() if ktp_data.tempat_lahir else None,
            age=age,
            is_adult=is_adult,
            nationality_code=nationality_code,
            nationality=nationality_name,
            full_residential_address=full_address,
            occupation=ktp_data.pekerjaan.title() if ktp_data.pekerjaan else None,
            marital_status=ktp_data.status_perkawinan.title() if ktp_data.status_perkawinan else None,
            registration_card_ready=ready_for_checkin,
        )

        return profile, warnings

    def _calculate_age(self, birth_date: Optional[date]) -> Optional[int]:
        """Calculates age in whole years from birth date."""
        if not birth_date:
            return None
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def _cross_validate_nik(self, ktp_data: KTPNormalized, warnings: List[CheckInWarning]) -> None:
        """Cross-checks decoded NIK demographic data against printed card data."""
        if len(ktp_data.nik) != 16:
            warnings.append(
                CheckInWarning(
                    code="INVALID_NIK_LENGTH",
                    message=f"NIK must be 16 digits long, found {len(ktp_data.nik)} characters.",
                    severity=WarningSeverity.CRITICAL,
                )
            )
            return

        detail = ktp_data.nik_detail
        if not detail:
            return

        # Check birth date mismatch
        if (
            detail.extracted_birth_date
            and ktp_data.tanggal_lahir
            and detail.extracted_birth_date != ktp_data.tanggal_lahir
        ):
            warnings.append(
                CheckInWarning(
                    code="NIK_DOB_MISMATCH",
                    message=(
                        f"Printed birth date ({ktp_data.tanggal_lahir}) does not match "
                        f"encoded NIK birth date ({detail.extracted_birth_date})."
                    ),
                    severity=WarningSeverity.WARNING,
                )
            )

        # Check gender mismatch
        if (
            detail.extracted_gender
            and ktp_data.jenis_kelamin != GenderEnum.UNKNOWN
            and detail.extracted_gender != ktp_data.jenis_kelamin
        ):
            warnings.append(
                CheckInWarning(
                    code="NIK_GENDER_MISMATCH",
                    message=(
                        f"Printed gender ({ktp_data.jenis_kelamin.value}) does not match "
                        f"encoded NIK gender ({detail.extracted_gender.value})."
                    ),
                    severity=WarningSeverity.WARNING,
                )
            )

    def _format_address(self, addr: AddressDetail) -> str:
        """Combines address components into a clean formatted string for hotel folios."""
        parts: List[str] = []

        if addr.street:
            parts.append(addr.street)

        rt_rw_part = ""
        if addr.rt and addr.rw:
            rt_rw_part = f"RT {addr.rt} / RW {addr.rw}"
        elif addr.rt:
            rt_rw_part = f"RT {addr.rt}"
        elif addr.rw:
            rt_rw_part = f"RW {addr.rw}"

        if rt_rw_part:
            parts.append(rt_rw_part)

        if addr.kel_desa:
            parts.append(f"Kel. {addr.kel_desa}" if not addr.kel_desa.upper().startswith("KEL") else addr.kel_desa)

        if addr.kecamatan:
            parts.append(f"Kec. {addr.kecamatan}" if not addr.kecamatan.upper().startswith("KEC") else addr.kecamatan)

        if addr.city:
            parts.append(addr.city)

        if addr.province:
            parts.append(addr.province)

        return ", ".join(parts) if parts else "Address Not Provided"
