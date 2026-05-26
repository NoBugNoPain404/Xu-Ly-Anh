import os
os.environ["FLAGS_use_mkldnn"] = "0"
import cv2
from pipeline.ekyc_pipeline import EKYCPipeline

def main():
    image_path = "./data/test1.jpg"
    image = cv2.imread(image_path)
    
    if image is None:
        raise ValueError(f"Cannot read image at path: {image_path}")

    pipeline = EKYCPipeline()

    result = pipeline.run(image)


    final_data = result["texts"]
    for field, value in final_data.items():
        print(f"{field:15}: {value}")
        

if __name__ == "__main__":
    main()