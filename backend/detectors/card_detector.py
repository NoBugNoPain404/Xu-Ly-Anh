from __future__ import annotations

from typing import Any
import cv2
import numpy as np
from inference_sdk import InferenceHTTPClient

from core.config import Config
from core.exceptions import CardNotFoundError, RoboflowAPIError


class CardDetector:
    def __init__(self) -> None:
        Config.validate()

        self.client = InferenceHTTPClient(
            api_url=Config.ROBOFLOW_API_BASE,
            api_key=Config.ROBOFLOW_API_KEY,
        )

    def detect_from_bytes(self, image_bytes: bytes) -> np.ndarray:

        if not image_bytes:
            raise CardNotFoundError("Input image bytes are empty")

        payload = self._call_roboflow(image_bytes=image_bytes)
        points = self._extract_polygon_from_response(payload)

        return np.asarray(points, dtype=np.float32)


    def _call_roboflow(self, image_bytes: bytes) -> dict[str, Any]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        result = self.client.infer(
            image,
            model_id=Config.ROBOFLOW_MODEL_ID,
        )

        if not result:
            raise RoboflowAPIError("Empty response from Roboflow")

        return result


    def _extract_polygon_from_response(self, payload: dict[str, Any]) -> list[list[float]]:
        predictions = payload.get("predictions", [])

        if not predictions:
            raise CardNotFoundError("Mô hình Roboflow không phát hiện được khung thẻ nào trong ảnh")

        best = max(predictions, key=lambda item: float(item.get("confidence", 0.0)))
        return self._extract_points(best)

    def _extract_points(self, prediction: dict[str, Any]) -> list[list[float]]:
        if "points" in prediction:
            return self._parse_points(prediction["points"])

        if all(k in prediction for k in ("x", "y", "width", "height")):
            x = float(prediction["x"])
            y = float(prediction["y"])
            w = float(prediction["width"])
            h = float(prediction["height"])
            return [
                [x - w / 2.0, y - h / 2.0],
                [x + w / 2.0, y - h / 2.0],
                [x + w / 2.0, y + h / 2.0],
                [x - w / 2.0, y + h / 2.0],
            ]

        raise CardNotFoundError("Khối dự đoán không chứa tọa độ polygon hoặc bounding box")

    def _parse_points(self, raw_points: Any) -> list[list[float]]:
        parsed = []
        for point in raw_points:
            parsed.append([float(point["x"]), float(point["y"])])
        return parsed