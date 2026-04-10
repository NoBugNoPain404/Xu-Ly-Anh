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
    ROBOFLOW_FIELD_MODEL_ID = os.getenv("FIELD_MODEL_ID")

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

        if not Config.ROBOFLOW_FIELD_MODEL_ID:
            raise ValueError("Missing FIELD_MODEL_ID in .env")


# Stage 4 - Image enhancement parameters for OCR preprocessing
CLAHE_CLIP_LIMIT = 1.2 
CLAHE_TILE_GRID_SIZE = (8, 8)
ADAPTIVE_BLOCK_SIZE = 15
ADAPTIVE_C = 10
MORPH_KERNEL_SIZE = (2, 2)

CARD_WIDTH = 856
CARD_HEIGHT = 540

# Tắt hoàn toàn offset và dynamic padding
ROI_Y_OFFSET_CONFIG = {
    "mode": "fixed",
    "fixed": 0.0,
    "base": 0.0,
    "slope": 0.0,
}

ROI_DYNAMIC_PADDING = {}

ROI = {
    "id_number":     (0.389, 0.398, 0.745, 0.461),
    "full_name":     (0.285, 0.544, 0.919, 0.598),
    "date_of_birth": (0.576, 0.613, 0.826, 0.657),
    "gender":        (0.460, 0.661, 0.553, 0.730),
    "nationality":   (0.815, 0.654, 0.971, 0.720),
    "home_town":     (0.283, 0.796, 0.985, 0.843),
    "address_line1": (0.682, 0.840, 0.951, 0.911), 
    "address_line2": (0.283, 0.920, 0.921, 0.993), 
    "expiry_date":   (0.000, 0.880, 0.280, 0.980),
}

ROI_PADDING = {
    # Tăng mạnh pad_top và pad_bottom lên 10-15 để hứng chữ bị xê dịch
    "id_number":     (8, 8, 4, 4),   
    "full_name":     (12, 12, 4, 4), # Nới rộng để không mất tên   
    "date_of_birth": (10, 10, 4, 4), # Nới rộng để không mất ngày sinh
    "gender":        (8, 8, 4, 4),
    "nationality":   (8, 8, 4, 4),
    "home_town":     (15, 12, 4, 4), # Nới rộng mạnh để không mất quê quán
    "address_line1": (15, 6, 4, 4),  
    "address_line2": (10, 10, 4, 4),   
    "expiry_date":   (10, 10, 6, 4),
}

ROI_MULTILINE_EXTRA_BOTTOM = {
    "full_name": 2,
    "home_town": 3,
    "address":   4,
}

OCR_PADDLE_CONFIG = {
    "lang": "vi",
}
OCR_MIN_HEIGHT_FOR_UPSCALE = 60
OCR_UPSCALE_FACTOR = 4 
OCR_BORDER_PAD = 10

# [ĐÃ SỬA] Hạ xuống 0.35 để bắt được các nhãn có font chữ siêu nhỏ hoặc mờ
OCR_MIN_CONFIDENCE = 0.35 
ANCHOR_ROI_PAD = 8