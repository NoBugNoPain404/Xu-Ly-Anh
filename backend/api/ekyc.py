from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from api.dependencies import validate_upload
from api.ekyc_schema import EKYCResponse
from pipeline.ekyc_pipeline import EKYCPipeline

router = APIRouter(prefix="/api/v1", tags=["ekyc"])


@lru_cache(maxsize=1)
def get_pipeline() -> EKYCPipeline:
    return EKYCPipeline()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/scan", response_model=EKYCResponse)
async def scan_cccd(
    file: UploadFile = File(...),
    _: None = Depends(validate_upload),
    pipeline: EKYCPipeline = Depends(get_pipeline),
) -> EKYCResponse:
    raw_bytes = await file.read()

    image = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid image data. Unable to decode upload.",
        )

    try:
        result = pipeline.run(image)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {exc}",
        ) from exc

    texts = result.get("texts", {})
    return EKYCResponse(**texts)
