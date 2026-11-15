"""Text cleaning and OCR normalization service.

Corrects OCR substitution artifacts, normalizes punctuation,
and prepares raw text lines for regex parsing.
"""

import re
from typing import List


class TextCleaner:
    """Provides targeted text cleaning routines for KTP documents."""

    # Common OCR character substitutions in numeric fields
    NUMERIC_SUBSTITUTIONS = {
        "O": "0", "o": "0", "D": "0", "Q": "0",
        "I": "1", "l": "1", "|": "1", "!": "1", "[": "1", "]": "1",
        "Z": "2", "z": "2",
        "E": "3",
        "A": "4",
        "S": "5", "s": "5", "§": "5",
        "G": "6", "b": "6",
        "T": "7",
        "B": "8",
        "g": "9", "q": "9",
    }

    # Label misread corrections
    LABEL_FIXES = [
        (r"(?i)\b(N1K|N!K|N\|K|NI K)\b", "NIK"),
        (r"(?i)\b(Narna|NAMA|Nam a)\b", "Nama"),
        (r"(?i)\b(Tempat\s*/?\s*Tg[li]\s*Lahir)\b", "Tempat/Tgl Lahir"),
        (r"(?i)\b(Jen[il]s\s*Kelam[il]n)\b", "Jenis Kelamin"),
        (r"(?i)\b(Gol\.?\s*Darah)\b", "Gol. Darah"),
        (r"(?i)\b(A[li]amat)\b", "Alamat"),
        (r"(?i)\b(RT\s*/\s*RW)\b", "RT/RW"),
        (r"(?i)\b(Ke[li]/?\s*Desa)\b", "Kel/Desa"),
        (r"(?i)\b(Kecamat[ao]n)\b", "Kecamatan"),
        (r"(?i)\b(Status\s*Perkaw[il]nan)\b", "Status Perkawinan"),
        (r"(?i)\b(Pekerja[ao]n)\b", "Pekerjaan"),
        (r"(?i)\b(Kewarganegara[ao]n)\b", "Kewarganegaraan"),
        (r"(?i)\b(Ber[li]aku\s*H[il]ngga)\b", "Berlaku Hingga"),
    ]

    @classmethod
    def clean_raw_lines(cls, text: str) -> List[str]:
        """Cleans and splits raw OCR text into normalized lines."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_lines = []

        for line in lines:
            line_clean = line
            for pattern, replacement in cls.LABEL_FIXES:
                line_clean = re.sub(pattern, replacement, line_clean)
            cleaned_lines.append(line_clean)

        return cleaned_lines

    @classmethod
    def clean_numeric_string(cls, raw_val: str) -> str:
        """Converts lookalike alphabetical characters to digits."""
        res = []
        for ch in raw_val:
            if ch.isdigit():
                res.append(ch)
            elif ch in cls.NUMERIC_SUBSTITUTIONS:
                res.append(cls.NUMERIC_SUBSTITUTIONS[ch])
        return "".join(res)

    @classmethod
    def strip_label_prefix(cls, line: str, label_keywords: List[str]) -> str:
        """Removes field label prefix and delimiter characters (e.g. 'Nama : John' -> 'John').

        Also strips common OCR colon misreads such as '|', '!', ':', ';', '=' or isolated '1'.
        Preserves valid starting alphabetic letters in values (e.g. 'ISLAM').
        """
        for kw in label_keywords:
            pattern = rf"(?i)^{re.escape(kw)}\s*[:=\-–;|!]*\s*"
            line = re.sub(pattern, "", line)

        # Strip remaining leading punctuation delimiters
        line = re.sub(r"^[:=\-–;|!]+\s*", "", line)
        # Strip isolated numeric '1' delimiter followed by space (common colon misread)
        line = re.sub(r"^1\s+", "", line)
        return line.strip()

    @classmethod
    def clean_name(cls, raw_name: str) -> str:
        """Cleans guest name by stripping noise characters, normalizing spacing, and pruning border artifacts."""
        name = re.sub(r"[^a-zA-Z\s.,'\-]", "", raw_name)
        # Strip stray trailing single letters like ' f' or ' |' from border artifacts if name already has multiple words
        words = name.split()
        if len(words) > 1 and len(words[-1]) == 1 and words[-1].lower() in ["f", "l", "i", "t", "x", "j"]:
            name = " ".join(words[:-1])
        name = re.sub(r"\s+", " ", name)
        return name.strip()
