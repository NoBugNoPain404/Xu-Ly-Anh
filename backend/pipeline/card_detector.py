from __future__ import annotations

from typing import Any
import base64
import cv2
import numpy as np

from inference_sdk import InferenceHTTPClient

from config import Config
from utils.exceptions import CardNotFoundError, RoboflowAPIError


class CardDetector:
    def __init__(self) -> None:
        Config.validate()

        self.client = InferenceHTTPClient(
            api_url=Config.ROBOFLOW_API_BASE,
            api_key=Config.ROBOFLOW_API_KEY,
        )

    # =========================================================
    # PUBLIC
    # =========================================================
    def detect_from_bytes(self, image_bytes: bytes) -> np.ndarray:
        """
        Return polygon points from Roboflow (NOT only 4 corners)
        """
        if not image_bytes:
            raise CardNotFoundError("Input image bytes are empty")

        payload = self._call_roboflow(image_bytes=image_bytes)
        points = self._extract_polygon_from_workflow(payload)

        return np.asarray(points, dtype=np.float32)


    # =========================================================
    # ROBOFLOW
    # =========================================================
    def _call_roboflow(self, image_bytes: bytes) -> dict[str, Any]:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        result = self.client.run_workflow(
            workspace_name=Config.ROBOFLOW_WORKSPACE,
            workflow_id=Config.ROBOFLOW_MODEL_ID,
            images={"image": image_b64},
            use_cache=True,
        )

        if not result:
            raise RoboflowAPIError("Empty response from Roboflow")

        return result[0]

    # =========================================================
    # PARSE ROBOFLOW RESPONSE
    # =========================================================
    def _extract_polygon_from_workflow(self, payload: dict[str, Any]) -> list[list[float]]:
        predictions_block = payload.get("predictions")

        if not predictions_block:
            raise CardNotFoundError("No predictions block in response")

        predictions = predictions_block.get("predictions", [])

        if not predictions:
            raise CardNotFoundError("No card detected")

        best = max(predictions, key=lambda item: float(item.get("confidence", 0.0)))
        return self._extract_points(best)

    def _extract_points(self, prediction: dict[str, Any]) -> list[list[float]]:
        # polygon points
        if "points" in prediction:
            return self._parse_points(prediction["points"])

        # bbox fallback
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

        raise CardNotFoundError("Card polygon not found")

    def _parse_points(self, raw_points: Any) -> list[list[float]]:
        parsed = []
        for point in raw_points:
            parsed.append([float(point["x"]), float(point["y"])])
        return parsed

