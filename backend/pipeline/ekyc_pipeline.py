from __future__ import annotations
from venv import logger

import cv2
import numpy as np

from core.config import CARD_HEIGHT, CARD_WIDTH

from detectors.yolo_field_detector import YoloFieldDetector
from enhancement.enhancer import ImageEnhancer
from detectors.card_detector import CardDetector
from ocr.ocr_engine import OCREngine
from postprocessor.postprocessor import Postprocessor

class EKYCPipeline:
    def __init__(self) -> None:
        self.detector = CardDetector()
        self.field_detector = YoloFieldDetector()
        self.enhancer = ImageEnhancer()
        self.ocr = OCREngine()
        self.postprocessor = Postprocessor()

    def run(self, image: np.ndarray):
        _, buffer = cv2.imencode(".jpg", image)
        image_bytes = buffer.tobytes()

        polygon = self.detector.detect_from_bytes(image_bytes)

        card = self._warp_from_polygon(image, polygon)

        enhanced = self.enhancer.enhance(card)

        rois = self.field_detector.extract(enhanced)

        raw_texts = self.ocr.recognize(rois)

        final_texts = self.postprocessor.process(raw_texts)

        print("Raw OCR outputs:", raw_texts)

        print("Final extracted data:", final_texts)

        return {
            "card": card,
            "enhanced": enhanced,
            "rois": rois,
            "raw_texts": raw_texts,
            "texts": final_texts,
        }

    def _warp_from_polygon(self, image: np.ndarray, polygon: np.ndarray) -> np.ndarray:
        corners = self._polygon_to_corners(polygon)
        ordered = self._order_corners(corners)

        tl, tr, br, bl = ordered

        width_top = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        max_width = int(max(width_top, width_bottom))

        height_right = np.linalg.norm(br - tr)
        height_left = np.linalg.norm(bl - tl)
        max_height = int(max(height_right, height_left))

        margin = 30 
        
        dst = np.array(
            [
                [margin, margin],                         
                [max_width + margin - 1, margin],         
                [max_width + margin - 1, max_height + margin - 1], 
                [margin, max_height + margin - 1],     
            ],
            dtype=np.float32,
        )
        
        new_width = max_width + 2 * margin
        new_height = max_height + 2 * margin

        matrix = cv2.getPerspectiveTransform(ordered, dst)
        
        warped = cv2.warpPerspective(image, matrix, (new_width, new_height))
        
        warped = cv2.resize(
            warped,
            (CARD_WIDTH, CARD_HEIGHT),
            interpolation=cv2.INTER_LINEAR,
        )

        return warped

    def _polygon_to_corners(self, polygon: np.ndarray) -> np.ndarray:
        pts = polygon.astype(np.float32)

        sums = pts.sum(axis=1)
        diffs = np.diff(pts, axis=1).reshape(-1)

        tl = pts[np.argmin(sums)]
        br = pts[np.argmax(sums)]
        tr = pts[np.argmin(diffs)]
        bl = pts[np.argmax(diffs)]

        return np.array([tl, tr, br, bl], dtype=np.float32)

    def _order_corners(self, corners: np.ndarray) -> np.ndarray:
        sums = corners.sum(axis=1)
        diffs = np.diff(corners, axis=1).reshape(-1)

        tl = corners[np.argmin(sums)]
        br = corners[np.argmax(sums)]
        tr = corners[np.argmin(diffs)]
        bl = corners[np.argmax(diffs)]

        return np.array([tl, tr, br, bl], dtype=np.float32)
    