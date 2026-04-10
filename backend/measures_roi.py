# scripts/measure_roi.py
import cv2

img = cv2.imread("enhanced.jpg")
h, w = img.shape[:2]
print(f"Size: {w}x{h}")
clicks = []

WINDOW = "Measure ROI"  # tên thống nhất 1 chỗ

def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        ratio_x, ratio_y = x / w, y / h
        clicks.append((ratio_x, ratio_y))
        print(f"  click {len(clicks)}: pixel=({x},{y})  ratio=({ratio_x:.3f}, {ratio_y:.3f})")

        if len(clicks) % 2 == 0:
            x1, y1 = clicks[-2]
            x2, y2 = clicks[-1]
            print(f"  → ROI: ({x1:.3f}, {y1:.3f}, {x2:.3f}, {y2:.3f})\n")

cv2.namedWindow(WINDOW)                    # tạo window trước
cv2.imshow(WINDOW, img)
cv2.setMouseCallback(WINDOW, on_mouse)     # gán đúng tên
cv2.waitKey(0)
cv2.destroyAllWindows()