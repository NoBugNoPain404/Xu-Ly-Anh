from __future__ import annotations

import cv2
import numpy as np

from config import (
    ROI,
    ROI_DYNAMIC_PADDING,
    ROI_MULTILINE_EXTRA_BOTTOM,
    ROI_PADDING,
    ROI_Y_OFFSET_CONFIG,
)


class ROIExtractor:

    def extract(self, image: np.ndarray) -> dict[str, np.ndarray]:
        """Crop all configured ROI fields from a rectified grayscale image."""
        height, width = image.shape[:2]
        rois: dict[str, np.ndarray] = {}

        for field, rel_box in ROI.items():
            x1, y1, x2, y2 = self._padded_box_pixels(field, rel_box, width, height)
            rois[field] = image[y1:y2, x1:x2]

        return rois

    def visualize(
        self,
        image: np.ndarray,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
    ) -> np.ndarray:
        """Draw corrected and padded ROI boxes on image for validation."""
        if image.ndim == 2:
            annotated = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            annotated = image.copy()

        height, width = image.shape[:2]

        for field, rel_box in ROI.items():
            x1, y1, x2, y2 = self._padded_box_pixels(field, rel_box, width, height)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            cv2.putText(
                annotated,
                field,
                (x1, max(0, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
                cv2.LINE_AA,
            )

        return annotated

    def _padded_box_pixels(
        self,
        field: str,
        rel_box: tuple[float, float, float, float],
        width: int,
        height: int,
    ) -> tuple[int, int, int, int]:
        rx1, ry1, rx2, ry2 = rel_box
        ry1, ry2 = self._apply_vertical_offset(ry1, ry2)

        x1 = int(rx1 * width)
        y1 = int(ry1 * height)
        x2 = int(rx2 * width)
        y2 = int(ry2 * height)

        y_center = (ry1 + ry2) / 2.0
        pad_top_base, pad_bottom_base, pad_left, pad_right = ROI_PADDING[field]
        dynamic_cfg = ROI_DYNAMIC_PADDING.get(field, {"base_pad": pad_top_base, "k": 0})
        dynamic_pad = int(round(float(dynamic_cfg["base_pad"]) + float(dynamic_cfg["k"]) * y_center))

        pad_top = max(pad_top_base, dynamic_pad)
        pad_bottom = max(pad_bottom_base, dynamic_pad)
        pad_bottom += int(ROI_MULTILINE_EXTRA_BOTTOM.get(field, 0))

        x1 -= pad_left
        x2 += pad_right
        y1 -= pad_top
        y2 += pad_bottom

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)

        return x1, y1, x2, y2

    def _apply_vertical_offset(self, ry1: float, ry2: float) -> tuple[float, float]:
        y_center = (ry1 + ry2) / 2.0
        box_height = ry2 - ry1

        mode = str(ROI_Y_OFFSET_CONFIG.get("mode", "adaptive")).lower()
        if mode == "fixed":
            offset = float(ROI_Y_OFFSET_CONFIG.get("fixed", 0.03))
        else:
            base = float(ROI_Y_OFFSET_CONFIG.get("base", 0.02))
            slope = float(ROI_Y_OFFSET_CONFIG.get("slope", 0.02))
            offset = base + slope * y_center

        shifted_center = min(1.0, max(0.0, y_center + offset))
        shifted_ry1 = shifted_center - box_height / 2.0
        shifted_ry2 = shifted_center + box_height / 2.0

        if shifted_ry1 < 0.0:
            shifted_ry2 = min(1.0, shifted_ry2 - shifted_ry1)
            shifted_ry1 = 0.0
        if shifted_ry2 > 1.0:
            overflow = shifted_ry2 - 1.0
            shifted_ry1 = max(0.0, shifted_ry1 - overflow)
            shifted_ry2 = 1.0

        return shifted_ry1, shifted_ry2
