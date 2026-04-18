import cv2
import sys
import os

# Add parent directory to path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from ai_engine.anpr_engine import ANPREngine

def test_ocr(image_path):
    print(f"Testing OCR on image: {image_path}")
    
    if not os.path.exists(image_path):
        print("Error: Image file not found.")
        return

    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not load image.")
        return

    print("Initializing ANPR Engine (EasyOCR)...")
    anpr = ANPREngine()
    
    # Normally, detector.py crops the car out first. 
    # For this test, we'll pass the whole image since the plate is large and clear.
    print("Extracting plate number...")
    plate = anpr.extract_plate_number(img)
    
    if plate:
        print(f"\nSUCCESS! OCR Extracted Plate: {plate}")
    else:
        print("\nFAILED: Could not extract a valid plate number from the image.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Path to the image file")
    args = parser.parse_args()
    
    test_ocr(args.image_path)
