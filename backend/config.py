import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env cùng thư mục với config.py
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    ROBOFLOW_API_BASE = os.getenv("ROBOFLOW_API_BASE")
    ROBOFLOW_API_KEY = os.getenv("API_KEY")
    ROBOFLOW_WORKSPACE = os.getenv("WORKSPACE")
    ROBOFLOW_MODEL_ID = os.getenv("MODEL_ID")

    @staticmethod
    def validate():
        if not Config.ROBOFLOW_API_BASE:
            raise ValueError("Missing ROBOFLOW_API_BASE in .env")

        if not Config.ROBOFLOW_API_KEY:
            raise ValueError("Missing API_KEY in .env")

        if not Config.ROBOFLOW_WORKSPACE:
            raise ValueError("Missing WORKSPACE in .env")

        if not Config.ROBOFLOW_MODEL_ID:
            raise ValueError("Missing MODEL_ID in .env")


# Stage 4 - Image enhancement parameters for OCR preprocessing
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_GRID_SIZE = (8, 8)
ADAPTIVE_BLOCK_SIZE = 15
ADAPTIVE_C = 10
MORPH_KERNEL_SIZE = (2, 2)

CARD_WIDTH = 856
CARD_HEIGHT = 540


ROI = {
    "id_number":     (0.285, 0.396, 0.951, 0.465),
    "full_name":     (0.282, 0.485, 0.943, 0.594),  # updated ROI
    "date_of_birth": (0.283, 0.620, 0.965, 0.654),
    "gender":        (0.279, 0.680, 0.553, 0.731),
    "nationality":   (0.561, 0.672, 0.971, 0.726),
    "home_town":     (0.287, 0.757, 0.787, 0.852),
    "address":       (0.282, 0.870, 0.936, 0.976),
    "expiry_date":   (0.000, 0.880, 0.280, 0.980),
}
# Tắt hoàn toàn offset và dynamic padding
ROI_Y_OFFSET_CONFIG = {
    "mode": "fixed",
    "fixed": 0.0,
    "base": 0.0,
    "slope": 0.0,
}

ROI_DYNAMIC_PADDING = {}

ROI_PADDING = {
    "id_number":     (2, 4, 4, 4),   # tăng bottom nếu bị cắt dưới
    "full_name":     (2, 6, 4, 4),   # tăng bottom vì chữ có dấu cao
    "date_of_birth": (2, 4, 4, 4),
    "gender":        (2, 4, 4, 4),
    "nationality":   (2, 4, 4, 4),
    "home_town":     (2, 8, 4, 4),   # multiline, cần bottom lớn hơn
    "address":       (2, 8, 4, 4),   # multiline
    "expiry_date":   (2, 4, 4, 4),
}

ROI_MULTILINE_EXTRA_BOTTOM = {
    "full_name": 2,
    "home_town": 3,
    "address":   4,
}