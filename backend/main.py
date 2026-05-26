from __future__ import annotations

import os

# Must be set before importing modules that may trigger PaddleOCR initialization.
os.environ["FLAGS_use_mkldnn"] = "0"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ekyc import router as ekyc_router
from core.config import Config

app = FastAPI(
    title="eKYC ID Card Scanner",
    description="Extract identity fields from Vietnamese CCCD card images.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ekyc_router)


@app.on_event("startup")
async def on_startup() -> None:
    Config.validate()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
