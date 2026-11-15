"""Image Preprocessing Service for optimizing KTP documents before OCR.

Applies resizing, grayscale conversion, deskewing, noise filtering,
contrast enhancement (CLAHE), and adaptive binarization.
"""

from typing import Tuple
import cv2
import numpy as np
from PIL import Image
import io

from app.core.exceptions import ImageProcessingError
from app.core.logging import logger


class ImagePreprocessor:
    """Preprocesses raw image bytes into an OCR-optimized grayscale/binary image."""

    def __init__(
        self,
        target_width: int = 1200,
        deskew: bool = True,
        clahe_clip_limit: float = 2.0,
        clahe_grid_size: int = 8,
    ):
        self.target_width = target_width
        self.deskew_enabled = deskew
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_grid_size = clahe_grid_size

    def decode_image(self, image_bytes: bytes) -> np.ndarray:
        """Decodes raw image bytes into an OpenCV BGR numpy array."""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                # Fallback via PIL
                pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return img
        except Exception as e:
            logger.error(f"Failed to decode image bytes: {e}")
            raise ImageProcessingError(f"Corrupt or unreadable image file: {str(e)}")

    def resize_to_width(self, image: np.ndarray, width: int) -> np.ndarray:
        """Resizes the image to a standardized width while maintaining aspect ratio."""
        h, w = image.shape[:2]
        if w == 0 or h == 0:
            raise ImageProcessingError("Invalid image dimensions (0x0).")

        if w == width:
            return image

        scaling_factor = width / float(w)
        target_height = int(h * scaling_factor)
        interpolation = cv2.INTER_CUBIC if scaling_factor > 1.0 else cv2.INTER_AREA
        return cv2.resize(image, (width, target_height), interpolation=interpolation)

    def deskew(self, gray_image: np.ndarray) -> np.ndarray:
        """Estimates skew angle and rotates the image to align horizontally."""
        try:
            # Invert colors: text as foreground (white) on dark background
            thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) < 50:
                return gray_image

            angle = cv2.minAreaRect(coords)[-1]
            # OpenCV minAreaRect returns angle in [-90, 0)
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            # Ignore minuscule rotations to avoid interpolation blur
            if abs(angle) < 0.5 or abs(angle) > 30:
                return gray_image

            (h, w) = gray_image.shape[:2]
            center = (w // 2, h // 2)
            rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                gray_image,
                rot_matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            return rotated
        except Exception as e:
            logger.warning(f"Deskew skipped due to error: {e}")
            return gray_image

    def enhance_contrast(self, gray_image: np.ndarray) -> np.ndarray:
        """Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) to balance lighting."""
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=(self.clahe_grid_size, self.clahe_grid_size),
        )
        return clahe.apply(gray_image)

    def denoise(self, gray_image: np.ndarray) -> np.ndarray:
        """Removes background grain and sensor noise using a bilateral filter."""
        return cv2.bilateralFilter(gray_image, d=7, sigmaColor=50, sigmaSpace=50)

    def binarize(self, gray_image: np.ndarray) -> np.ndarray:
        """Applies Otsu binarization to produce high-contrast binary black & white image."""
        _, binary = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return binary

    def preprocess(self, image_bytes: bytes) -> Tuple[np.ndarray, np.ndarray]:
        """Executes full preprocessing pipeline.

        Returns:
            Tuple[np.ndarray, np.ndarray]: (enhanced_grayscale_image, binarized_image)
        """
        img = self.decode_image(image_bytes)
        resized = self.resize_to_width(img, self.target_width)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        if self.deskew_enabled:
            gray = self.deskew(gray)

        enhanced = self.enhance_contrast(gray)
        denoised = self.denoise(enhanced)
        binarized = self.binarize(denoised)

        return denoised, binarized
