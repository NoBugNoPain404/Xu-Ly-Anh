from __future__ import annotations

import logging

import cv2
import numpy as np
from paddleocr import PaddleOCR

from core.config import (
    OCR_BORDER_PAD,
    OCR_MIN_CONFIDENCE,
    OCR_MIN_HEIGHT_FOR_UPSCALE,
    OCR_PADDLE_CONFIG,
    OCR_UPSCALE_FACTOR,
)

logger = logging.getLogger("ocr_engine")

class OCREngine:

    def __init__(self) -> None:
        self._ocr = PaddleOCR(
            lang=OCR_PADDLE_CONFIG["lang"],
            use_gpu=False,   
            show_log=False   
        )

    def detect_layout(self, image: np.ndarray) -> list[dict]:
        result = self._ocr.ocr(image, cls=True)
        lines: list[dict] = []

        if not result or result[0] is None:
            return lines

        for line in result[0]:
            box = line[0]      
            text_info = line[1] 
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
        results: dict[str, str] = {}

        for field_name, image in rois.items():
            try:
                processed = self._prepare_image(field_name, image)
                
                image_bgr = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
                
                ocr_result = self._ocr.ocr(image_bgr, cls=True)
                
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
        
        for line in result[0]:
            text_info = line[1]
            text = text_info[0]
            score = text_info[1]
            
            if text and float(score) >= OCR_MIN_CONFIDENCE:
                texts.append(str(text).strip())

        return " ".join(texts).strip()  