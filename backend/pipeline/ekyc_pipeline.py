from __future__ import annotations
from venv import logger

import cv2
import numpy as np

from config import CARD_HEIGHT, CARD_WIDTH

from .yolo_field_detector import YoloFieldDetector
from .enhancer import ImageEnhancer
from .card_detector import CardDetector
from .ocr_engine import OCREngine
from .postprocessor import Postprocessor

class EKYCPipeline:
    def __init__(self) -> None:
        self.detector = CardDetector()
        self.field_detector = YoloFieldDetector()
        self.enhancer = ImageEnhancer()
        self.ocr = OCREngine()
        self.postprocessor = Postprocessor()

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

        # 5. Detect field crops using Roboflow Workflow
        rois = self.field_detector.extract(enhanced)

        # 6. OCR nhận diện văn bản thô từ các vùng đã cắt
        raw_texts = self.ocr.recognize(rois)

        # 7. HẬU XỬ LÝ (Lọc rác, định dạng số, ngày tháng)
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

    # =========================
    # Warp logic (keep nguyên)
    # =========================
    def _warp_from_polygon(self, image: np.ndarray, polygon: np.ndarray) -> np.ndarray:
        corners = self._polygon_to_corners(polygon)
        ordered = self._order_corners(corners)

        tl, tr, br, bl = ordered

        # Tính toán kích thước thẻ gốc
        width_top = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        max_width = int(max(width_top, width_bottom))

        height_right = np.linalg.norm(br - tr)
        height_left = np.linalg.norm(bl - tl)
        max_height = int(max(height_right, height_left))

        # --- PHẦN SỬA ĐỔI: THÊM MARGIN ---
        margin = 30  # Nới rộng mỗi cạnh thêm 30 pixel
        
        # Điểm đích mới sẽ không bắt đầu từ (0,0) mà lùi ra ngoài một khoảng margin
        dst = np.array(
            [
                [margin, margin],                         # Top-left
                [max_width + margin - 1, margin],          # Top-right
                [max_width + margin - 1, max_height + margin - 1], # Bottom-right
                [margin, max_height + margin - 1],         # Bottom-left
            ],
            dtype=np.float32,
        )
        
        # Kích thước ảnh mới bao gồm cả phần nới rộng
        new_width = max_width + 2 * margin
        new_height = max_height + 2 * margin

        # Tính ma trận biến đổi dựa trên các điểm đã ordered và dst mới
        matrix = cv2.getPerspectiveTransform(ordered, dst)
        
        # Warp với kích thước mới
        warped = cv2.warpPerspective(image, matrix, (new_width, new_height))
        
        # Resize về kích thước chuẩn định nghĩa trong config (giữ tỉ lệ thẻ)
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
    