import cv2
from pipeline.ekyc_pipeline import EKYCPipeline
from config import Config


image = cv2.imread("./midv500/official.jpg")

pipeline = EKYCPipeline()
result = pipeline.run(image)

# ✅ Save full card (sau warp)
cv2.imwrite("card.jpg", result["card"])

# ✅ Save enhanced image
cv2.imwrite("enhanced.jpg", result["enhanced"])

# ✅ Save ROI overlay for visual validation (boxes after correction + padding)
roi_overlay = pipeline.roi_extractor.visualize(result["enhanced"])
cv2.imwrite("roi_overlay.jpg", roi_overlay)

# ✅ Save all ROIs
for name, roi in result["rois"].items():
    cv2.imwrite(f"roi_{name}.jpg", roi)

print("Saved card.jpg, enhanced.jpg and ROI images")