"""NIK (Nomor Induk Kependudukan) validation and parsing service.

Validates 16-digit structure, decodes province/city codes, extracts birth date,
and evaluates gender using the Indonesian statutory female +40 day rule.
"""

from datetime import date
from typing import Dict, Optional, Tuple
from app.schemas.ktp import GenderEnum, NIKDetail


class NIKValidator:
    """Validator and decoder for Indonesian National Identity Numbers."""

    # Official Indonesian Kemendagri 2-digit Province Codes
    PROVINCE_CODES: Dict[str, str] = {
        "11": "ACEH",
        "12": "SUMATERA UTARA",
        "13": "SUMATERA BARAT",
        "14": "RIAU",
        "15": "JAMBI",
        "16": "SUMATERA SELATAN",
        "17": "BENGKULU",
        "18": "LAMPUNG",
        "19": "KEPULAUAN BANGKA BELITUNG",
        "21": "KEPULAUAN RIAU",
        "31": "DKI JAKARTA",
        "32": "JAWA BARAT",
        "33": "JAWA TENGAH",
        "34": "DAERAH ISTIMEWA YOGYAKARTA",
        "35": "JAWA TIMUR",
        "36": "BANTEN",
        "51": "BALI",
        "52": "NUSA TENGGARA BARAT",
        "53": "NUSA TENGGARA TIMUR",
        "61": "KALIMANTAN BARAT",
        "62": "KALIMANTAN TENGAH",
        "63": "KALIMANTAN SELATAN",
        "64": "KALIMANTAN TIMUR",
        "65": "KALIMANTAN UTARA",
        "71": "SULAWESI UTARA",
        "72": "SULAWESI TENGAH",
        "73": "SULAWESI SELATAN",
        "74": "SULAWESI TENGGARA",
        "75": "GORONTALO",
        "76": "SULAWESI BARAT",
        "81": "MALUKU",
        "82": "MALUKU UTARA",
        "91": "PAPUA BARAT",
        "92": "PAPUA BARAT DAYA",
        "94": "PAPUA",
        "95": "PAPUA SELATAN",
        "96": "PAPUA TENGAH",
        "97": "PAPUA PEGUNUNGAN",
    }

    @classmethod
    def validate_and_decode(cls, raw_nik: str) -> NIKDetail:
        """Validates NIK length and structure, decoding demographic data."""
        clean_nik = "".join(filter(str.isdigit, raw_nik))

        if len(clean_nik) != 16:
            return NIKDetail(
                nik=clean_nik,
                is_valid_format=False,
            )

        province_code = clean_nik[0:2]
        city_code = clean_nik[2:4]
        district_code = clean_nik[4:6]
        raw_day = int(clean_nik[6:8])
        raw_month = int(clean_nik[8:10])
        raw_year = int(clean_nik[10:12])
        sequence_num = clean_nik[12:16]

        province_name = cls.PROVINCE_CODES.get(province_code, "UNKNOWN PROVINCE")

        birth_date, gender = cls._decode_birth_and_gender(raw_day, raw_month, raw_year)

        is_valid = bool(
            province_code in cls.PROVINCE_CODES
            and birth_date is not None
            and 1 <= int(sequence_num) <= 9999
        )

        return NIKDetail(
            nik=clean_nik,
            is_valid_format=is_valid,
            province_code=province_code,
            province_name=province_name,
            city_code=city_code,
            district_code=district_code,
            extracted_birth_date=birth_date,
            extracted_gender=gender,
            sequence_number=sequence_num,
        )

    @classmethod
    def _decode_birth_and_gender(
        cls, raw_day: int, raw_month: int, raw_year: int
    ) -> Tuple[Optional[date], GenderEnum]:
        """Decodes birth date and gender using the female +40 day rule.

        In Indonesian NIK standard:
        - Male birth day is 1-31.
        - Female birth day has 40 added: 41-71.
        """
        if 41 <= raw_day <= 71:
            actual_day = raw_day - 40
            gender = GenderEnum.FEMALE
        elif 1 <= raw_day <= 31:
            actual_day = raw_day
            gender = GenderEnum.MALE
        else:
            return None, GenderEnum.UNKNOWN

        if not (1 <= raw_month <= 12):
            return None, gender

        # Century estimation
        current_year = date.today().year
        century = 2000 if raw_year <= (current_year % 100) else 1900
        full_year = century + raw_year

        try:
            birth_date = date(full_year, raw_month, actual_day)
            return birth_date, gender
        except ValueError:
            return None, gender
