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

        # Step 1: Chuyển sang ảnh xám
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Step 2: Làm mịn nhẹ nhàng bằng Bilateral Filter để khử nhiễu
        # d=7 là đủ để làm phẳng nền mà không làm mờ nét chữ.
        smoothed = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)

        # Step 3: Tăng cường độ tương phản thông minh bằng CLAHE
        # Đây là bước quan trọng nhất để làm nổi bật nét chữ khỏi nền.
        # Tăng clipLimit lên 3.0 để tăng cường độ tương phản mạnh hơn.
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(smoothed)

        # Step 4: Cân bằng trắng (White Balancing) nhẹ nhàng
        # Vẫn dùng để đẩy nền về màu trắng nhưng với mốc rộng hơn để bảo vệ nét chữ.
        brightest_pixel = np.percentile(contrast_enhanced, 98) # Lấy mốc 98%
        enhanced_float = contrast_enhanced.astype(np.float32)
        
        # Kéo nền về màu trắng (255)
        normalized = (enhanced_float / brightest_pixel) * 255
        normalized = np.clip(normalized, 0, 255).astype(np.uint8)

        # Step 5: Làm sắc nét mạnh (Strong Sharpening)
        # Sử dụng một kernel mạnh hơn để khôi phục lại các nét chữ bị mờ.
        kernel = np.array([[-1, -1, -1], [-1, 10, -1], [-1, -1, -1]]) / 2.0
        final_img = cv2.filter2D(normalized, -1, kernel)

        return final_img