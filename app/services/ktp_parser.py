"""KTP Document Parsing Service.

Parses cleaned OCR text into structured raw and normalized KTP schemas
using regex pattern matching, heuristic heuristics, and error-tolerant extraction.
"""

from datetime import date, datetime
import re
from typing import List, Optional
from app.schemas.ktp import (
    AddressDetail,
    GenderEnum,
    KTPNormalized,
    RawKTPFields,
)
from app.services.nik_validator import NIKValidator
from app.services.text_cleaner import TextCleaner


class KTPParser:
    """Extracts and normalizes Indonesian KTP data from OCR text lines."""

    def __init__(self, nik_validator: Optional[NIKValidator] = None):
        self.nik_validator = nik_validator or NIKValidator()

    def parse(self, raw_text: str) -> KTPNormalized:
        """Parses raw text and returns normalized KTP data."""
        lines = TextCleaner.clean_raw_lines(raw_text)
        raw_fields = self._extract_raw_fields(lines)
        return self._normalize_fields(raw_fields)

    def _extract_raw_fields(self, lines: List[str]) -> RawKTPFields:
        """Extracts raw key-value fields from text lines using regular expressions."""
        raw = RawKTPFields()

        for idx, line in enumerate(lines):
            line_stripped = line.strip()

            # 1. Provinsi
            if re.search(r"(?i)\bPROVINSI\b", line_stripped):
                raw.provinsi = line_stripped

            # 2. Kota / Kabupaten
            elif re.search(r"(?i)\b(KOTA|KABUPATEN)\b", line_stripped):
                raw.kota_kabupaten = line_stripped

            # 3. NIK
            elif re.search(r"(?i)\bNIK\b", line_stripped) or re.search(r"\b\d{16}\b", line_stripped):
                val_after_label = TextCleaner.strip_label_prefix(line_stripped, ["NIK", "N1K", "N!K"])
                digits = TextCleaner.clean_numeric_string(val_after_label)
                m = re.search(r"\d{16}", digits)
                if m:
                    raw.nik = m.group(0)
                elif len(digits) >= 14:
                    raw.nik = digits[:16]

            # 4. Nama
            elif re.search(r"(?i)\bNama\b", line_stripped):
                name_val = TextCleaner.strip_label_prefix(line_stripped, ["Nama", "NAMA"])
                raw.nama = TextCleaner.clean_name(name_val)

            # 5. Tempat / Tgl Lahir
            elif re.search(r"(?i)\bTempat", line_stripped) or re.search(r"(?i)Tgl\s*Lahir", line_stripped):
                val = TextCleaner.strip_label_prefix(
                    line_stripped,
                    ["Tempat/Tgl Lahir", "Tempat/Tanggal Lahir", "Tempat", "Tgl Lahir", "Tempat/Tgi Lahir"],
                )
                date_match = re.search(r"(\d{1,2})[\s\-/.]{1,2}(\d{1,2})[\s\-/.]{1,2}(\d{4})", val)
                if date_match:
                    d, m, y = date_match.groups()
                    raw.tanggal_lahir = f"{int(d):02d}-{int(m):02d}-{y}"
                    place = val[:date_match.start()].rstrip(" ,-/:")
                    raw.tempat_lahir = TextCleaner.clean_name(place)
                else:
                    raw.tempat_lahir = val.strip()

            # 6. Jenis Kelamin & Gol Darah
            elif re.search(r"(?i)Jenis\s*Kelamin", line_stripped):
                val = line_stripped.upper()
                if "LAKI" in val:
                    raw.jenis_kelamin = "LAKI-LAKI"
                elif "PEREMPUAN" in val:
                    raw.jenis_kelamin = "PEREMPUAN"

                blood_match = re.search(r"(?i)Gol\.?\s*Darah\s*[:=\-]?\s*([ABO\-+]{1,2})", line_stripped)
                if blood_match:
                    raw.golongan_darah = blood_match.group(1).upper()

            # 7. Gol. Darah (if isolated line)
            elif re.search(r"(?i)Gol\.?\s*Darah", line_stripped) and not raw.golongan_darah:
                m = re.search(r"(?i)Gol\.?\s*Darah\s*[:=\-]?\s*([ABO\-+]{1,2})", line_stripped)
                if m:
                    raw.golongan_darah = m.group(1).upper()

            # 8. Alamat
            elif re.search(r"(?i)\bAlamat\b", line_stripped):
                raw.alamat = TextCleaner.strip_label_prefix(line_stripped, ["Alamat", "ALAMAT"])

            # 9. RT / RW
            elif re.search(r"(?i)\bRT\b|\bRW\b", line_stripped):
                raw.rt_rw = TextCleaner.strip_label_prefix(line_stripped, ["RT/RW", "RT", "RW"])

            # 10. Kel / Desa
            elif re.search(r"(?i)\b(Kel|Desa|Kelurahan)\b", line_stripped):
                raw.kel_desa = TextCleaner.strip_label_prefix(line_stripped, ["Kel/Desa", "Kel.", "Desa", "Kelurahan"])

            # 11. Kecamatan
            elif re.search(r"(?i)\bKecamatan\b", line_stripped):
                raw.kecamatan = TextCleaner.strip_label_prefix(line_stripped, ["Kecamatan", "KECAMATAN"])

            # 12. Agama
            elif re.search(r"(?i)\bAgama\b", line_stripped):
                raw.agama = TextCleaner.strip_label_prefix(line_stripped, ["Agama", "AGAMA"]).upper()

            # 13. Status Perkawinan
            elif re.search(r"(?i)Status\s*Perkawinan", line_stripped):
                raw.status_perkawinan = TextCleaner.strip_label_prefix(
                    line_stripped, ["Status Perkawinan", "STATUS PERKAWINAN"]
                ).upper()

            # 14. Pekerjaan
            elif re.search(r"(?i)\bPekerjaan\b", line_stripped):
                raw.pekerjaan = TextCleaner.strip_label_prefix(line_stripped, ["Pekerjaan", "PEKERJAAN"]).upper()

            # 15. Kewarganegaraan
            elif re.search(r"(?i)Kewarganegaraan", line_stripped):
                val = line_stripped.upper()
                if "WNI" in val:
                    raw.kewarganegaraan = "WNI"
                elif "WNA" in val:
                    raw.kewarganegaraan = "WNA"
                else:
                    raw.kewarganegaraan = TextCleaner.strip_label_prefix(line_stripped, ["Kewarganegaraan"]).upper()

            # 16. Berlaku Hingga
            elif re.search(r"(?i)Berlaku\s*Hingga", line_stripped):
                raw.berlaku_hingga = TextCleaner.strip_label_prefix(
                    line_stripped, ["Berlaku Hingga", "BERLAKU HINGGA"]
                ).upper()

        return raw

    def _normalize_fields(self, raw: RawKTPFields) -> KTPNormalized:
        """Converts raw parsed fields into strongly typed normalized models."""
        nik_clean = raw.nik or ""
        nik_detail = self.nik_validator.validate_and_decode(nik_clean) if nik_clean else None

        # Parse birth date
        parsed_birth_date: Optional[date] = None
        if raw.tanggal_lahir:
            try:
                parsed_birth_date = datetime.strptime(raw.tanggal_lahir, "%d-%m-%Y").date()
            except ValueError:
                pass

        # If birth date missing or invalid in text, fallback to NIK decoded birth date
        if not parsed_birth_date and nik_detail and nik_detail.extracted_birth_date:
            parsed_birth_date = nik_detail.extracted_birth_date

        # Normalize Gender
        gender = GenderEnum.UNKNOWN
        if raw.jenis_kelamin:
            if "LAKI" in raw.jenis_kelamin.upper():
                gender = GenderEnum.MALE
            elif "PEREMPUAN" in raw.jenis_kelamin.upper():
                gender = GenderEnum.FEMALE
        elif nik_detail and nik_detail.extracted_gender:
            gender = nik_detail.extracted_gender

        # Parse RT/RW components
        rt_val, rw_val = None, None
        if raw.rt_rw:
            parts = re.split(r"[/\-]", raw.rt_rw)
            if len(parts) >= 2:
                rt_val = "".join(filter(str.isdigit, parts[0]))
                rw_val = "".join(filter(str.isdigit, parts[1]))
            elif len(parts) == 1:
                rt_val = "".join(filter(str.isdigit, parts[0]))

        address = AddressDetail(
            street=raw.alamat,
            rt=rt_val,
            rw=rw_val,
            kel_desa=raw.kel_desa,
            kecamatan=raw.kecamatan,
            city=raw.kota_kabupaten,
            province=raw.provinsi,
        )

        return KTPNormalized(
            nik=nik_clean,
            nama=(raw.nama or "UNKNOWN GUEST").upper(),
            tempat_lahir=(raw.tempat_lahir or "").upper() or None,
            tanggal_lahir=parsed_birth_date,
            jenis_kelamin=gender,
            golongan_darah=raw.golongan_darah,
            alamat=address,
            agama=raw.agama,
            status_perkawinan=raw.status_perkawinan,
            pekerjaan=raw.pekerjaan,
            kewarganegaraan=raw.kewarganegaraan or "WNI",
            berlaku_hingga=raw.berlaku_hingga or "SEUMUR HIDUP",
            nik_detail=nik_detail,
        )
