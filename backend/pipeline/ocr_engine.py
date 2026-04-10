from __future__ import annotations

import logging

import cv2
import numpy as np
from paddleocr import PaddleOCR

from config import (
    OCR_BORDER_PAD,
    OCR_MIN_CONFIDENCE,
    OCR_MIN_HEIGHT_FOR_UPSCALE,
    OCR_PADDLE_CONFIG,
    OCR_UPSCALE_FACTOR,
)

logger = logging.getLogger("ocr_engine")

class OCREngine:
    """Stage 6 OCR using PaddleOCR for robust Vietnamese CCCD text extraction."""

    def __init__(self) -> None:
        # Khởi tạo một lần để dùng nhiều lần
        self._ocr = PaddleOCR(
            lang=OCR_PADDLE_CONFIG["lang"],
            use_gpu=False,    # Đảm bảo ổn định trên CPU (Fedora)
            show_log=False    # Tắt log cấu hình khi khởi động
        )

    def detect_layout(self, image: np.ndarray) -> list[dict]:
        """Detect full-card text layout on warped color image using PaddleOCR."""
        # [SỬA]: Đổi .predict thành .ocr và bật cls=True để nhận diện hướng chữ
        result = self._ocr.ocr(image, cls=True)
        lines: list[dict] = []

        # PaddleOCR trả về list lồng nhau: [[ [box, (text, score)], ... ]]
        if not result or result[0] is None:
            return lines

        for line in result[0]:
            box = line[0]      # Tọa độ 4 góc: [[x,y], [x,y], [x,y], [x,y]]
            text_info = line[1] # Tuple: (văn bản, độ tự tin)
            text = text_info[0]
            score = text_info[1]

            if not text or float(score) < OCR_MIN_CONFIDENCE:
                continue

            xs = [point[0] for point in box]
            ys = [point[1] for point in box]
            
            lines.append(
                {
                    "text": str(text).strip(),
                    "score": float(score),
                    "y_center": (min(ys) + max(ys)) / 2,
                    "x_center": (min(xs) + max(xs)) / 2,
                    "box": box,
                    "y_top": int(min(ys)),
                    "y_bottom": int(max(ys)),
                    "x_left": int(min(xs)),
                    "x_right": int(max(xs)),
                }
            )

        return sorted(lines, key=lambda line: line["y_center"])

    def recognize(self, rois: dict[str, np.ndarray]) -> dict[str, str]:
        """Recognize raw text for each ROI and keep the pipeline resilient to failures."""
        results: dict[str, str] = {}

        for field_name, image in rois.items():
            try:
                # Tiền xử lý ảnh xám
                processed = self._prepare_image(field_name, image)
                
                # PaddleOCR yêu cầu ảnh 3 kênh (BGR)
                image_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                
                # Sửa lỗi: Thay predict bằng ocr(), dùng cls=True để xử lý hướng chữ
                ocr_result = self._ocr.ocr(image_bgr, cls=True)
                
                # Trích xuất văn bản từ kết quả của Paddle
                results[field_name] = self._extract_text(ocr_result)
            except Exception as error:
                logger.warning("OCR failed for field '%s': %s", field_name, error)
                results[field_name] = ""

        return results

    def _prepare_image(self, field_name: str, image: np.ndarray) -> np.ndarray:
        if image.ndim != 2:
            raise ValueError(f"Expected 2D grayscale image for field '{field_name}', got shape {image.shape}")

        h = image.shape[0]
        if h < OCR_MIN_HEIGHT_FOR_UPSCALE:
            scale = OCR_UPSCALE_FACTOR
            image = cv2.resize(
                image,
                (int(image.shape[1] * scale), int(h * scale)),
                # Đổi sang LANCZOS4 để chữ mượt và không bị răng cưa khi phóng to gấp 4 lần
                interpolation=cv2.INTER_LANCZOS4, 
            )

        pad = OCR_BORDER_PAD
        image = cv2.copyMakeBorder(
            image, pad, pad, pad, pad,
            cv2.BORDER_CONSTANT,
            value=255,
        )

        return image

    def _extract_text(self, result: list | None) -> str:
        """Parse PaddleOCR output: [[ [box, (text, score)], ... ]]"""
        if not result or result[0] is None:
            return ""

        texts: list[str] = []
        
        # PaddleOCR trả về list lồng nhau, result[0] chứa các dòng nhận diện được
        for line in result[0]:
            # line[0] là tọa độ box, line[1] là tuple (text, confidence)
            text_info = line[1]
            text = text_info[0]
            score = text_info[1]
            
            # Lọc kết quả dựa trên độ tự tin (Confidence)
            if text and float(score) >= OCR_MIN_CONFIDENCE:
                texts.append(str(text).strip())

        return " ".join(texts).strip()  