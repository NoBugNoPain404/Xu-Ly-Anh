from __future__ import annotations

import logging
import cv2
import numpy as np
from inference_sdk import InferenceHTTPClient

from config import Config
from utils.exceptions import RoboflowAPIError

logger = logging.getLogger("yolo_field_detector")


class YoloFieldDetector:
    """Stage 5 detector using standard Roboflow Object Detection inference."""

    def __init__(self) -> None:
        self.client = InferenceHTTPClient(
            api_url=Config.ROBOFLOW_API_BASE,
            api_key=Config.ROBOFLOW_API_KEY,
        )

        self.class_map = {
            "id": "id_number",
            "name": "full_name",
            "dob": "date_of_birth",
            "gender": "gender",
            "nationality": "nationality",
            "origin_place": "home_town",
            "current_place": "address",
            # Đã xóa expiry_date
        }

    def extract(self, image: np.ndarray) -> dict[str, np.ndarray]:
        result = self.client.infer(
            image, 
            model_id=Config.ROBOFLOW_FIELD_MODEL_ID
        )

        if not result or "predictions" not in result:
            raise RoboflowAPIError("Empty or invalid response from Field Detection Model")

        predictions = result["predictions"]

        if not isinstance(predictions, list):
            raise RoboflowAPIError("Invalid prediction payload format")

        predictions = sorted(predictions, key=lambda p: float(p.get("y", 0.0)) if isinstance(p, dict) else 0)

        height, width = image.shape[:2]
        rois: dict[str, np.ndarray] = {}

        for pred in predictions:
            if not isinstance(pred, dict):
                continue

            yolo_class = pred.get("class")
            system_key = self.class_map.get(str(yolo_class))
            
            if not system_key:
                continue

            if system_key == "address":
                if "address_line1" not in rois:
                    system_key = "address_line1"
                else:
                    system_key = "address_line2"

            cx = float(pred.get("x", 0.0))
            cy = float(pred.get("y", 0.0))
            box_width = float(pred.get("width", 0.0))
            box_height = float(pred.get("height", 0.0))

            pad_x = 5
            pad_y = 5

            x1 = max(0, int(cx - box_width / 2) - pad_x)
            y1 = max(0, int(cy - box_height / 2) - pad_y)
            x2 = min(width, int(cx + box_width / 2) + pad_x)
            y2 = min(height, int(cy + box_height / 2) + pad_y)

            crop = image[y1:y2, x1:x2]
            if crop.size == 0:
                logger.warning("Empty crop for class '%s'", yolo_class)
                continue

            rois[system_key] = crop

        return rois