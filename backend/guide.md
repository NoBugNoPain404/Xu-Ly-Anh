# Developer Guide – eKYC ID Card Scanner

## Overview

This backend processes Vietnamese ID card (CCCD) images to extract identity information. It uses the Roboflow API for card detection and a local image processing pipeline for the remaining steps.

The key design insight is that Roboflow returns a dense polygon — a large set of points tracing the card boundary — not just 4 corners. Converting that polygon into exactly 4 reliable corner points is its own dedicated stage in the pipeline.

---

## Architecture

The project is split into three clearly separated layers:

**API Layer** handles HTTP communication — receiving uploaded images from clients and returning structured JSON responses. It has no image processing logic.

**Pipeline Layer** handles all image processing. Each stage is isolated in its own file with a single responsibility. Stages are chained together by the orchestrator `ekyc_pipeline.py`.

**Output Layer** handles exporting the final result to JSON or PDF format.

---

## Pipeline Stages

### Stage 1 – Card Detection (`card_detector.py`)
Sends the raw uploaded image directly to the Roboflow API. Roboflow returns a dense polygon — a large set of points (typically 20–100+) tracing the full boundary of the card with high spatial detail. This stage returns those raw polygon points as-is, without any modification. No preprocessing is applied to the image before this API call.

### Stage 2 – Corner Extraction (`corner_extractor.py`)
Reduces the dense polygon from Stage 1 down to exactly 4 corner points suitable for Perspective Transform. This is a dedicated stage because naively picking 4 points from a dense polygon produces unstable or inaccurate results.

The approach:
- Compute the convex hull of all polygon points to remove any inward noise.
- Apply `approxPolyDP` with a tuned epsilon to simplify the hull toward 4 vertices.
- If the result has more than 4 points, select the 4 extreme points using a scoring strategy (minimum and maximum of x+y and x−y), which reliably identifies top-left, top-right, bottom-right, and bottom-left regardless of card rotation.
- Sort the final 4 points into a consistent clockwise order before passing to the next stage.

This approach is significantly more robust than using 4-point detection directly, because the dense polygon from Roboflow accurately captures curved or partially obscured card edges that a 4-point model would miss.

### Stage 3 – Perspective Transform (`perspective.py`)
Takes the 4 ordered corner points from Stage 2 and applies a geometric correction to produce a flat, rectangular card image. Operates on the same image that was sent to the Roboflow API to ensure coordinate alignment. Output is a standardized 856×540px card image.

### Stage 4 – Image Enhancement (`enhancer.py`)
Improves text clarity for OCR. Applies grayscale conversion, CLAHE for contrast normalization across uneven lighting, Adaptive Thresholding for binarization, and light morphological operations to sharpen text edges. This is the first and only image preprocessing step in the pipeline — all prior stages work on the original color image.

### Stage 5 – ROI Extraction (`roi_extractor.py`)
Crops specific regions of the warped card image based on relative coordinates defined in `config.py`. Each region corresponds to one information field: ID number, full name, date of birth, gender, nationality, place of origin, address, and expiry date.

### Stage 6 – OCR Engine (`ocr_engine.py`)
Runs text recognition on each cropped ROI image. Uses Tesseract with Vietnamese language support and per-field page segmentation mode configuration. Returns a dictionary mapping each field name to its raw recognized text string.

### Stage 7 – Postprocessor (`postprocessor.py`)
Cleans and validates the raw OCR output. Applies regex patterns to extract and verify each field, corrects common OCR errors (digit-letter confusion), normalizes Vietnamese Unicode to NFC form, and builds the final structured dictionary ready for the API response.

---

## Data Flow

```
Client uploads image
        ↓
FastAPI Route
  – Validates file type and size
  – Decodes bytes to image array
        ↓
EKYCPipeline.run(image)
  – card_detector      → dense polygon (many points)
  – corner_extractor   → 4 ordered corner points
  – perspective        → flat card 856×540
  – enhancer           → high-contrast grayscale image
  – roi_extractor      → dict of cropped region images
  – ocr_engine         → dict of raw text per field
  – postprocessor      → cleaned structured dict
        ↓
FastAPI Response → JSON
```

---

## Why a Dense Polygon, Not 4 Points

Roboflow Instance Segmentation returns a dense polygon because it is solving a general segmentation problem — it does not assume the object is a perfect rectangle. This has meaningful advantages for this use case:

- Cards photographed at steep angles have edges that appear curved in the image plane. A dense polygon captures this curvature accurately.
- Cards with rounded physical corners or minor physical damage are still correctly bounded.
- Partial occlusion (a finger covering a corner) does not collapse the entire detection — the visible portions of the boundary are still accurately traced.

The tradeoff is that `warpPerspective` requires exactly 4 points, so the Corner Extraction stage exists specifically to bridge between the rich polygon output and the 4-point requirement of the geometric transform.

---

## Key Design Decisions

**No preprocessing before the Roboflow API call.**
The raw image is sent directly to Roboflow without any prior modification. The Roboflow model was trained with augmentation covering varied lighting, blur, and rotation, so it handles raw images reliably. Preprocessing before detection would risk degrading information that the model relies on.

**Corner extraction is a separate stage, not part of card detection.**
Mixing polygon-to-corner conversion inside `card_detector.py` would conflate two distinct responsibilities: network communication and geometric computation. Keeping them separate makes each independently testable and replaceable.

**Perspective Transform operates on the image sent to the API.**
The polygon points returned by Roboflow are in the coordinate space of the image that was uploaded. The transform must be applied to that exact image. If a different image (different resolution or crop) were used, the coordinates would not align.

**Image preprocessing happens after warp, not before detection.**
Grayscale conversion, CLAHE, and thresholding are only applied after the card has been cropped and straightened. At that point the image is smaller and contains only card content, making these operations more accurate and computationally cheaper.

**Each pipeline stage is independently testable.**
Every class in the `pipeline/` folder can be instantiated and called in isolation without running the full server. The `scripts/index.py` file serves as a standalone script for manual testing and inspection of Roboflow API responses.

---

## Configuration

All tunable parameters are centralized in `config.py`. This includes:

- `CARD_SIZE` – Output dimensions after Perspective Transform (856×540)
- `APPROX_EPSILON` – Epsilon multiplier for polygon simplification in corner extraction
- `ROI` – Relative coordinates (x1, y1, x2, y2 as ratios) for each information field
- `ROBOFLOW_WORKSPACE` and `ROBOFLOW_WORKFLOW_ID` – API routing
- OCR language and page segmentation mode per field
- Server host, port, and file upload limits

Sensitive values (API keys) are stored in `.env` and never committed to version control.

---

## File Responsibilities

| File | Responsibility |
|------|----------------|
| `main.py` | Create FastAPI app, register routers, configure CORS |
| `config.py` | All parameters in one place |
| `.env` | API_KEY and other secrets |
| `api/routes/ekyc.py` | POST /scan endpoint |
| `api/schemas/ekyc_schema.py` | Pydantic response model |
| `api/dependencies.py` | File type and size validation |
| `pipeline/card_detector.py` | Roboflow API call → raw dense polygon points |
| `pipeline/corner_extractor.py` | Dense polygon → 4 ordered corner points |
| `pipeline/perspective.py` | 4 corners → flat rectified card image |
| `pipeline/enhancer.py` | Improve image quality for OCR |
| `pipeline/roi_extractor.py` | Crop information regions from warped card |
| `pipeline/ocr_engine.py` | Read text from each cropped region |
| `pipeline/postprocessor.py` | Clean, validate, and structure OCR output |
| `pipeline/ekyc_pipeline.py` | Chain all stages in order |
| `output/json_writer.py` | Save result as JSON file |
| `output/pdf_writer.py` | Save result as PDF file |
| `utils/image_utils.py` | polygon_to_corners, order_corners helpers |
| `utils/visualizer.py` | Draw debug overlays: polygon, corners, ROI boxes |
| `scripts/index.py` | Manual test script for Roboflow API |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/scan` | Upload card image, returns extracted JSON |
| `GET` | `/api/v1/health` | Health check |

---

## Output JSON Format

```
{
  "id_number":     "012345678901",
  "full_name":     "NGUYEN VAN A",
  "date_of_birth": "01/01/1990",
  "gender":        "Male",
  "nationality":   "Vietnamese",
  "home_town":     "Ha Noi",
  "address":       "123 Example Street, Ha Noi",
  "expiry_date":   "01/01/2035"
}
```

---

## Running the Server

Install dependencies, set the `API_KEY` in `.env`, then start the server with uvicorn. The interactive API documentation is available at `/docs` once the server is running.
