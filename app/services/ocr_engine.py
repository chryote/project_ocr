"""Tesseract OCR Engine wrapper service.

Manages execution of pytesseract, language configuration, PSM/OEM modes,
and confidence score extraction.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil
import subprocess
from typing import List, Optional
import numpy as np
import pytesseract
from pytesseract import Output

from app.core.exceptions import OCRExecutionError
from app.core.logging import logger


@dataclass
class WordBox:
    """Bounding box and confidence for an individual OCR word."""
    text: str
    confidence: float
    left: int
    top: int
    width: int
    height: int
    line_num: int


@dataclass
class OCRResult:
    """Structured result returned by the OCR engine."""
    raw_text: str
    average_confidence: float
    words: List[WordBox] = field(default_factory=list)
    language_used: str = "eng"


class TesseractOCREngine:
    """Encapsulates interaction with Tesseract OCR binary."""

    def __init__(
        self,
        tesseract_cmd: str,
        tessdata_prefix: Optional[str] = None,
        default_lang: str = "ind+eng",
        fallback_lang: str = "eng",
        psm: int = 6,
        oem: int = 3,
        timeout: int = 15,
    ):
        self.tesseract_cmd = tesseract_cmd
        self.tessdata_prefix = str(Path(tessdata_prefix).resolve()) if tessdata_prefix else None
        self.default_lang = default_lang
        self.fallback_lang = fallback_lang
        self.psm = psm
        self.oem = oem
        self.timeout = timeout

        self._configure_environment()

    def _configure_environment(self) -> None:
        """Sets the executable path and tessdata directory."""
        if os.path.isfile(self.tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        else:
            resolved_path = shutil.which(self.tesseract_cmd)
            if resolved_path:
                pytesseract.pytesseract.tesseract_cmd = resolved_path
            else:
                logger.warning(
                    f"Tesseract binary not found at configured path: {self.tesseract_cmd}. "
                    "Defaulting to system PATH."
                )

        if self.tessdata_prefix and os.path.isdir(self.tessdata_prefix):
            os.environ["TESSDATA_PREFIX"] = self.tessdata_prefix

    def get_available_languages(self) -> List[str]:
        """Queries Tesseract for installed traineddata languages."""
        try:
            return pytesseract.get_languages()
        except Exception as e:
            logger.warning(f"Failed to query Tesseract languages: {e}")
            return ["eng"]

    def _resolve_language(self) -> str:
        """Determines best available language, falling back if necessary."""
        available = self.get_available_languages()
        langs_requested = self.default_lang.split("+")
        supported = [l for l in langs_requested if l in available]

        if supported:
            return "+".join(supported)
        if self.fallback_lang in available:
            return self.fallback_lang
        return "eng"

    def execute_ocr(self, image: np.ndarray, custom_psm: Optional[int] = None) -> OCRResult:
        """Executes OCR on an image and returns text and confidence metrics."""
        psm_to_use = custom_psm if custom_psm is not None else self.psm
        lang_to_use = self._resolve_language()

        config = f"--psm {psm_to_use} --oem {self.oem}".strip()

        try:
            # Extract detailed word-level data and confidences
            ocr_data = pytesseract.image_to_data(
                image,
                lang=lang_to_use,
                config=config,
                output_type=Output.DICT,
                timeout=self.timeout,
            )

            words: List[WordBox] = []
            confidences: List[float] = []
            text_lines: List[str] = []
            current_line_num = -1
            current_line_words: List[str] = []

            n_boxes = len(ocr_data.get("text", []))
            for i in range(n_boxes):
                text = ocr_data["text"][i].strip()
                conf_val = float(ocr_data["conf"][i])

                if text:
                    words.append(
                        WordBox(
                            text=text,
                            confidence=max(0.0, conf_val) / 100.0,
                            left=int(ocr_data["left"][i]),
                            top=int(ocr_data["top"][i]),
                            width=int(ocr_data["width"][i]),
                            height=int(ocr_data["height"][i]),
                            line_num=int(ocr_data["line_num"][i]),
                        )
                    )
                    if conf_val > 0:
                        confidences.append(conf_val)

                line_num = int(ocr_data["line_num"][i])
                if line_num != current_line_num:
                    if current_line_words:
                        text_lines.append(" ".join(current_line_words))
                        current_line_words = []
                    current_line_num = line_num

                if text:
                    current_line_words.append(text)

            if current_line_words:
                text_lines.append(" ".join(current_line_words))

            raw_text = "\n".join(text_lines)
            avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0

            return OCRResult(
                raw_text=raw_text,
                average_confidence=round(avg_conf, 4),
                words=words,
                language_used=lang_to_use,
            )

        except (subprocess.TimeoutExpired, TimeoutError):
            logger.error("Tesseract OCR execution timed out.")
            raise OCRExecutionError("OCR execution timed out.")
        except pytesseract.TesseractError as te:
            logger.error(f"Tesseract OCR runtime error: {te}")
            raise OCRExecutionError(f"Tesseract OCR failure: {str(te)}")
        except Exception as e:
            logger.error(f"Tesseract execution failed: {e}")
            raise OCRExecutionError(f"Tesseract OCR unexpected failure: {str(e)}")
