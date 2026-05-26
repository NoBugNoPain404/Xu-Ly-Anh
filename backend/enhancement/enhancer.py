from __future__ import annotations

import cv2
import numpy as np


class ImageEnhancer:
    """Stage 4 - Advanced image enhancement to improve text/background contrast."""

    def __init__(self) -> None:
        """Initialize ImageEnhancer."""
        pass

    def enhance(self, image: np.ndarray) -> np.ndarray:
        """
        Main entry point for image enhancement.
        Focuses on adaptive histogram equalization and sharpening.
        """
        if image is None or image.size == 0:
            return image

        img = image.copy()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


        smoothed = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(smoothed)

        brightest_pixel = np.percentile(contrast_enhanced, 98) 
        enhanced_float = contrast_enhanced.astype(np.float32)
        
        normalized = (enhanced_float / brightest_pixel) * 255
        normalized = np.clip(normalized, 0, 255).astype(np.uint8)

        kernel = np.array([[-1, -1, -1], [-1, 10, -1], [-1, -1, -1]]) / 2.0
        final_img = cv2.filter2D(normalized, -1, kernel)

        return final_img