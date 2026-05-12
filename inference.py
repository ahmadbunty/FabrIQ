"""
Inference Script for FabrIQ Fabric Defect Detection
Supports both Classification and Object Detection modes
"""

import argparse
from pathlib import Path
from ultralytics import YOLO
import cv2
import numpy as np

# Detection / classification labels (7 defect classes; order = class index 0..6)
CLASSES = [
    'contamination',
    'selvet',
    'gray_stitch',
    'cut',
    'baekra',
    'color_issue',
    'stain',
]

def classify_image(model_path, image_path, conf_threshold=0.25):
    """Classify a single image (classification mode)"""
    model = YOLO(model_path)
    
    results = model(image_path, conf=conf_threshold)
    
    # Get predictions
    probs = results[0].probs
    top1_idx = probs.top1
    top1_conf = probs.top1conf.item()
    
    predicted_class = CLASSES[top1_idx]
    
    print(f"\n📸 Image: {image_path}")
    print(f"   Predicted Class: {predicted_class}")
    print(f"   Confidence: {top1_conf:.4f}")
    
    # Show top 5 predictions
    top5 = probs.top5
    top5conf = probs.top5conf
    print(f"\n   Top 5 Predictions:")
    for i, (idx, conf) in enumerate(zip(top5, top5conf), 1):
        print(f"   {i}. {CLASSES[idx]}: {conf:.4f}")
    
    return predicted_class, top1_conf, results

def detect_defects(model_path, image_path, conf_threshold=0.25):
    """Detect defects with bounding boxes (detection mode)"""
    model = YOLO(model_path)
    
    results = model(image_path, conf=conf_threshold)
    
    # Get detections
    detections = results[0]
    
    print(f"\n📸 Image: {image_path}")
    print(f"   Detections: {len(detections.boxes)}")
    
    # Process each detection
    for i, box in enumerate(detections.boxes, 1):
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = CLASSES[cls]
        
        # Get bounding box coordinates
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        
        print(f"\n   Detection {i}:")
        print(f"      Class: {class_name}")
        print(f"      Confidence: {conf:.4f}")
        print(f"      Bounding Box: ({x1:.0f}, {y1:.0f}) to ({x2:.0f}, {y2:.0f})")
    
    return results

def visualize_results(results, image_path, output_path=None, mode='detection'):
    """Visualize and save results"""
    # Load image
    img = cv2.imread(str(image_path))
    
    if mode == 'detection':
        # Draw bounding boxes
        annotated = results[0].plot()
    else:
        # For classification, just show the image with text
        annotated = img.copy()
        probs = results[0].probs
        top1_idx = probs.top1
        top1_conf = probs.top1conf.item()
        predicted_class = CLASSES[top1_idx]
        
        # Add text
        text = f"{predicted_class}: {top1_conf:.2f}"
        cv2.putText(annotated, text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Save or show
    if output_path:
        cv2.imwrite(str(output_path), annotated)
        print(f"\n💾 Saved visualization to: {output_path}")
    else:
        cv2.imshow('Result', annotated)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description='FabrIQ Defect Detection Inference')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to model file (e.g., runs/classify/fabriq_defect_classification/weights/best.pt)')
    parser.add_argument('--source', type=str, required=True,
                       help='Path to image or directory of images')
    parser.add_argument('--mode', type=str, choices=['classification', 'detection'], default='classification',
                       help='Inference mode: classification or detection')
    parser.add_argument('--conf', type=float, default=0.25,
                       help='Confidence threshold')
    parser.add_argument('--save', action='store_true',
                       help='Save visualization results')
    parser.add_argument('--output', type=str, default='results',
                       help='Output directory for saved results')
    
    args = parser.parse_args()
    
    model_path = Path(args.model)
    source_path = Path(args.source)
    
    if not model_path.exists():
        print(f"❌ Error: Model file not found: {model_path}")
        return
    
    if not source_path.exists():
        print(f"❌ Error: Source path not found: {source_path}")
        return
    
    # Process single image or directory
    if source_path.is_file():
        images = [source_path]
    else:
        images = list(source_path.glob("*.jpg")) + list(source_path.glob("*.png"))
    
    print(f"🔍 Processing {len(images)} image(s)...")
    
    output_dir = Path(args.output)
    if args.save:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    for img_path in images:
        if args.mode == 'classification':
            predicted_class, confidence, results = classify_image(
                model_path, img_path, args.conf
            )
        else:
            results = detect_defects(model_path, img_path, args.conf)
        
        if args.save:
            output_file = output_dir / f"{img_path.stem}_result.jpg"
            visualize_results(results, img_path, output_file, args.mode)

if __name__ == "__main__":
    main()

