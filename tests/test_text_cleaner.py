"""Unit tests for TextCleaner service."""

from app.services.text_cleaner import TextCleaner


def test_clean_numeric_string_substitutions():
    """Verifies lookalike characters in numeric strings are correctly mapped."""
    # O -> 0, I -> 1, Z -> 2, S -> 5, B -> 8
    raw = "317IOIZS00B"
    cleaned = TextCleaner.clean_numeric_string(raw)
    assert cleaned == "31710125008"


def test_clean_name():
    """Verifies non-alphabet noise and excess spaces are removed from names."""
    raw = "  BUDI!  SANTOSO, S.Kom.  "
    cleaned = TextCleaner.clean_name(raw)
    assert cleaned == "BUDI SANTOSO, S.Kom."


def test_strip_label_prefix_standard():
    """Verifies standard label with colon is stripped cleanly."""
    line = "Nama : AHMAD DAHLAN"
    val = TextCleaner.strip_label_prefix(line, ["Nama", "NAMA"])
    assert val == "AHMAD DAHLAN"


def test_strip_label_prefix_ocr_delimiters():
    """Verifies label followed by misread colon (| or 1 or !) is stripped cleanly."""
    assert TextCleaner.strip_label_prefix("Alamat 1 JL. SUDIRMAN", ["Alamat"]) == "JL. SUDIRMAN"
    assert TextCleaner.strip_label_prefix("NIK | 3171011505900001", ["NIK"]) == "3171011505900001"
    assert TextCleaner.strip_label_prefix("Agama ! ISLAM", ["Agama"]) == "ISLAM"


def test_clean_raw_lines_replaces_ocr_typos():
    """Verifies that line cleaner fixes common misread keywords."""
    raw_text = (
        "N1K : 1234567890123456\n"
        "Narna : TEST USER\n"
        "Tempat/Tgi Lahir : BANDUNG\n"
        "Jenls Kelamln : LAKI-LAKI\n"
        "Gol Darah : O\n"
        "Aiamat : JL. ASIA AFRIKA\n"
    )
    cleaned = TextCleaner.clean_raw_lines(raw_text)
    assert any("NIK" in line for line in cleaned)
    assert any("Nama" in line for line in cleaned)
    assert any("Tempat/Tgl Lahir" in line for line in cleaned)
    assert any("Jenis Kelamin" in line for line in cleaned)
    assert any("Gol. Darah" in line for line in cleaned)
    assert any("Alamat" in line for line in cleaned)
