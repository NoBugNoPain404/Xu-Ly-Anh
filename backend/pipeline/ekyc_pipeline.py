from __future__ import annotations

import cv2
import numpy as np

from config import CARD_HEIGHT, CARD_WIDTH

from .enhancer import ImageEnhancer
from .card_detector import CardDetector
from .roi_extractor import ROIExtractor


class EKYCPipeline:
    def __init__(self) -> None:
        self.detector = CardDetector()
        self.roi_extractor = ROIExtractor()
        self.enhancer = ImageEnhancer()

    def run(self, image: np.ndarray):
        # 1. Encode image -> bytes (for Roboflow)
        _, buffer = cv2.imencode(".jpg", image)
        image_bytes = buffer.tobytes()

        # 2. Detect card polygon
        polygon = self.detector.detect_from_bytes(image_bytes)

        # 3. Warp to top-down view
        card = self._warp_from_polygon(image, polygon)

        # 4. Enhance image (contrast, sharpness...)
        enhanced = self.enhancer.enhance(card)

        # 5. Extract ROIs (with field-specific padding from config)
        rois = self.roi_extractor.extract(enhanced)

        return {
            "card": card,
            "enhanced": enhanced,
            "rois": rois,
        }

    # =========================
    # Warp logic (keep nguyên)
    # =========================
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

        max_width = max(max_width, 1)
        max_height = max(max_height, 1)

        dst = np.array(
            [
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1],
            ],
            dtype=np.float32,
        )

        matrix = cv2.getPerspectiveTransform(ordered, dst)
        warped = cv2.warpPerspective(image, matrix, (max_width, max_height))
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
    