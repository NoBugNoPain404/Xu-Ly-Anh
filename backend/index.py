import os
os.environ["FLAGS_use_mkldnn"] = "0"
import cv2
from pipeline.ekyc_pipeline import EKYCPipeline

def main():
    # 1. Load image
    image_path = "./data/test3.jpg"
    image = cv2.imread(image_path)
    
    if image is None:
        raise ValueError(f"Cannot read image at path: {image_path}")

    # 2. Khởi tạo Pipeline (Đã bao gồm Postprocessor bên trong)
    pipeline = EKYCPipeline()

    # 3. Chạy toàn bộ quy trình
    result = pipeline.run(image)

    # 4. Lưu kết quả debug
    cv2.imwrite("card.jpg", result["card"])
    cv2.imwrite("enhanced.jpg", result["enhanced"])
    
    # (Đã xóa phần vẽ ROI tĩnh vì hiện tại bạn đang cắt ảnh động bằng YOLO)

    # 5. In kết quả cuối cùng đã được làm sạch
    print("\n" + "="*40)
    print("      EKYC FINAL SYSTEM RESULT      ")
    print("="*40)
    
    final_data = result["texts"]
    for field, value in final_data.items():
        print(f"{field:15}: {value}")
        
    print("="*40)
    print("Hệ thống đã tự động lọc rác và định dạng dữ liệu.")

if __name__ == "__main__":
    main()