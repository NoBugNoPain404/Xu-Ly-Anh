# Project Structure – eKYC ID Card Scanner

```
ekyc_backend/
│
├── main.py                          # FastAPI app entry point
├── config.py                        # Global configuration (all pipeline + server params)
├── requirements.txt                 # All required libraries
├── .env                             # Environment variables (API_KEY, secrets)
│
├── api/                             # FastAPI layer
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── ekyc.py                  # POST /scan endpoint
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── ekyc_schema.py           # Pydantic request/response models
│   └── dependencies.py              # Shared dependencies (file validation, etc.)
│
├── pipeline/                        # Image processing – one file per stage
│   ├── __init__.py
│   ├── card_detector.py             # Stage 1 – Call Roboflow API, return raw polygon points
│   ├── corner_extractor.py          # Stage 2 – Reduce polygon points to 4 precise corners
│   ├── perspective.py               # Stage 3 – Perspective Transform (warpPerspective)
│   ├── enhancer.py                  # Stage 4 – CLAHE, Adaptive Threshold, Morphology
│   ├── roi_extractor.py             # Stage 5 – Crop each information region (ROI)
│   ├── ocr_engine.py                # Stage 6 – OCR text recognition
│   ├── postprocessor.py             # Stage 7 – Regex, validate, clean, build dict
│   └── ekyc_pipeline.py             # Orchestrator – chains all stages together
│
├── output/                          # Export results
│   ├── __init__.py
│   ├── json_writer.py               # Export extracted info to JSON file
│   └── pdf_writer.py                # Export extracted info + card image to PDF file
│
├── utils/
│   ├── __init__.py
│   ├── image_utils.py               # Shared helpers: order_corners, polygon_to_corners
│   ├── visualizer.py                # Debug: draw polygon/ROI boxes on image
│   └── file_utils.py                # Handle upload paths, temp files
│
├── scripts/
│   └── index.py                     # Standalone test script (manual testing only)
│
├── tests/
│   ├── test_pipeline.py             # Unit tests for each pipeline stage
│   ├── test_api.py                  # Integration tests for API endpoints
│   └── test_images/
│       ├── sample_01.jpg
│       └── sample_02.jpg
│
├── storage/
│   ├── uploads/                     # Temporarily store uploaded images
│   └── results/                     # Store output JSON and PDF files
│
└── logs/
    └── app.log                      # Application logs
```
