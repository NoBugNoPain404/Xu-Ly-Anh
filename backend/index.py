import os
os.environ["FLAGS_use_mkldnn"] = "0"
import cv2
from pipeline.ekyc_pipeline import EKYCPipeline

def main():
    # 1. Load image
    image_path = "./data/test5.jpg"
    image = cv2.imread(image_path)
    
    if image is None:
        raise ValueError(f"Cannot read image at path: {image_path}")

    # 2. Khởi tạo Pipeline (Đã bao gồm Postprocessor bên trong)
    pipeline = EKYCPipeline()

    # 3. Chạy toàn bộ quy trình
    result = pipeline.run(image)

    
    # (Đã xóa phần vẽ ROI tĩnh vì hiện tại bạn đang cắt ảnh động bằng YOLO)

    # 5. In kết quả cuối cùng đã được làm sạch

    final_data = result["texts"]
    for field, value in final_data.items():
        print(f"{field:15}: {value}")
        

if __name__ == "__main__":
    main()