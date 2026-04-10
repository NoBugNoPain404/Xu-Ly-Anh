from __future__ import annotations

import cv2
import numpy as np

from config import (
    ADAPTIVE_BLOCK_SIZE,
    ADAPTIVE_C,
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_GRID_SIZE,
    MORPH_KERNEL_SIZE,
)


class ImageEnhancer:
    """Preprocess warped card images into OCR-friendly binary grayscale output."""

    def enhance(self, image: np.ndarray) -> np.ndarray:
        """Apply grayscale, CLAHE, adaptive thresholding, and morphological closing."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(
            clipLimit=CLAHE_CLIP_LIMIT,
            tileGridSize=CLAHE_TILE_GRID_SIZE,
        )
        contrast = clahe.apply(gray)

        binary = cv2.adaptiveThreshold(
            contrast,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            ADAPTIVE_BLOCK_SIZE,
            ADAPTIVE_C,
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, MORPH_KERNEL_SIZE)
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return closed
