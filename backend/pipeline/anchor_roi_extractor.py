from __future__ import annotations

import logging
import re
import unicodedata

import numpy as np

from config import ANCHOR_ROI_PAD

logger = logging.getLogger("anchor_roi_extractor")

class AnchorExtractionError(Exception):
    pass

class AnchorBasedROIExtractor:
    """Stage 5 replacement - Dynamic ROI extraction using anchor labels.

    Instead of fixed relative coordinates, this extractor:
    1. Receives the full OCR layout (from OCREngine.detect_layout())
    2. Searches for each field's known label anchor in the detected lines
    3. Crops the value region from the enhanced image dynamically

    This is robust to card position shifts, slight rotations, and
    resolution changes - as long as the printed labels are readable.
    """

    # [ĐÃ SỬA] Thêm các biến thể lỗi font phổ biến của PaddleOCR
    _ANCHORS: dict[str, list[str]] = {
        "id_number": ["so / no", "no.", "so/no", "so:", "number", "so/"],
        "full_name": ["ho va ten", "full name", "hoten", "hovaten"],
        "date_of_birth": ["ngay sinh", "date of birth", "ngaysinh", "dob"],
        "gender": ["gioi tinh", "sex", "gioitinh"],
        "nationality": ["quoc tich", "nationality", "quoctich"],
        "home_town": ["que quan", "place of origin", "quequan"],
        "address": ["noi thuong tru", "place of residence", "thuongtru", "noithuongtru"],
        "expiry_date": ["co gia tri den", "date of expiry", "expiry", "gia tri den", "gia tri"],
    }

    @staticmethod
    def _normalize_for_matching(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        normalized = normalized.encode("ascii", errors="ignore").decode("ascii")
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9/\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _find_anchor(self, layout: list[dict], field_name: str) -> dict | None:
        keywords = self._ANCHORS[field_name]
        for line in layout:
            line_text = self._normalize_for_matching(str(line.get("text", "")))
            for keyword in keywords:
                if keyword in line_text:
                    return line
        return None

    def _find_value_line(self, layout: list[dict], anchor_line: dict, field_name: str) -> list[dict]:
        anchor_idx = -1
        for idx, line in enumerate(layout):
            if line.get("y_center") == anchor_line.get("y_center") and line.get("x_left") == anchor_line.get("x_left"):
                anchor_idx = idx
                break

        if anchor_idx < 0:
            return []

        same_row_right: list[dict] = []
        anchor_y = float(anchor_line["y_center"])
        anchor_right = int(anchor_line["x_right"])
        
        # [ĐÃ SỬA]: Tăng dung sai chiều dọc từ 15 lên 35 pixel
        for line in layout:
            if abs(float(line["y_center"]) - anchor_y) <= 35 and int(line["x_left"]) > anchor_right - 10:
                same_row_right.append(line)

        value_lines: list[dict] = []
        
        # Nếu tìm thấy chữ bên phải nhãn (cùng dòng), ưu tiên lấy block gần nhãn nhất
        if same_row_right:
            closest_right = min(same_row_right, key=lambda line: line["x_left"])
            value_lines.append(closest_right)

        lines_needed = 2 if field_name in {"home_town", "address"} else 1
        current_idx = anchor_idx + 1
        
        # [ĐÃ SỬA]: Bổ sung chốt chặn an toàn (tránh vớt nhầm sang nhãn khác)
        while len(value_lines) < lines_needed and current_idx < len(layout):
            candidate = layout[current_idx]
            
            candidate_text = self._normalize_for_matching(str(candidate.get("text", "")))
            is_another_label = False
            for kws in self._ANCHORS.values():
                if any(kw in candidate_text for kw in kws):
                    is_another_label = True
                    break
                    
            if is_another_label:
                break 
                
            if candidate not in value_lines:
                value_lines.append(candidate)
                
            current_idx += 1

        return value_lines

    def _crop_from_image(self, image: np.ndarray, lines: list[dict], pad: int) -> np.ndarray:
        y_top = min(int(line["y_top"]) for line in lines) - pad
        y_bottom = max(int(line["y_bottom"]) for line in lines) + pad
        x_left = min(int(line["x_left"]) for line in lines) - pad
        x_right = max(int(line["x_right"]) for line in lines) + pad

        y_top = max(0, y_top)
        y_bottom = min(image.shape[0], y_bottom)
        x_left = max(0, x_left)
        x_right = min(image.shape[1], x_right)

        return image[y_top:y_bottom, x_left:x_right]

    def extract(self, image: np.ndarray, layout: list[dict]) -> dict[str, np.ndarray]:
        output: dict[str, np.ndarray] = {}

        for field in self._ANCHORS:
            anchor = self._find_anchor(layout, field)
            if anchor is None:
                logger.warning("Anchor not found for field: %s", field)
                continue

            value_lines = self._find_value_line(layout, anchor, field)
            if not value_lines:
                logger.warning("Value line not found for field: %s", field)
                continue

            crop = self._crop_from_image(image, value_lines, pad=ANCHOR_ROI_PAD)
            if crop.size == 0:
                logger.warning("Empty crop generated for field: %s", field)
                continue

            output[field] = crop

        if len(output) < 4:
            logger.error(
                "AnchorBasedROIExtractor: only %d fields detected, falling back to fixed ROI",
                len(output),
            )
            raise AnchorExtractionError()

        return output