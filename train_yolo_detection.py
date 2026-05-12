"""
YOLOv8 Object Detection Training Script for FabrIQ Fabric Defect Detection
This script trains a detection model that can predict bounding boxes around defects.
Note: Requires YOLO-format annotation files (.txt) with bounding boxes.
"""

import os
from pathlib import Path
from ultralytics import YOLO
import yaml

# Configuration
DATASET_PATH = Path("FabrIQ_Final_Dataset")
MODEL_TYPE = "yolov8n.pt"  # Detection model
# Auto-detect device
try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    if DEVICE == "cpu":
        EPOCHS = 30
        IMG_SIZE = 416  # Smaller for CPU
        BATCH_SIZE = 4
    else:
        EPOCHS = 100
        IMG_SIZE = 640
        BATCH_SIZE = 16
except:
    DEVICE = "cpu"
    EPOCHS = 10
    IMG_SIZE = 416
    BATCH_SIZE = 4

# 7 defect classes (order must match fabriq_detection_data.yaml and trained weights)
CLASSES = [
    'contamination',
    'selvet',
    'gray_stitch',
    'cut',
    'baekra',
    'color_issue',
    'stain',
]

def create_data_yaml():
    """Create data.yaml configuration file for YOLO detection"""
    dataset_path = Path("FabrIQ_YOLO_Detection_Dataset")
    
    data_config = {
        'path': str(dataset_path.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'nc': len(CLASSES),
        'names': {i: cls for i, cls in enumerate(CLASSES)}
    }
    
    yaml_path = Path("fabriq_detection_data.yaml")
    with open(yaml_path, 'w') as f:
        yaml.dump(data_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Created data configuration: {yaml_path}")
    return yaml_path

def prepare_detection_dataset():
    """Prepare dataset structure for YOLO object detection"""
    print("📁 Preparing dataset structure for YOLO object detection...")
    
    yolo_dataset = Path("FabrIQ_YOLO_Detection_Dataset")
    
    # Create directory structure
    for split in ['train', 'val']:
        (yolo_dataset / split / 'images').mkdir(parents=True, exist_ok=True)
        (yolo_dataset / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    # Copy images
    for split in ['train', 'val']:
        source_dir = DATASET_PATH / split / 'images'
        
        if not source_dir.exists():
            print(f"⚠️ Warning: {source_dir} does not exist!")
            continue
        
        print(f"   Copying {split} images...")
        image_count = 0
        
        for img_file in source_dir.glob("*.jpg"):
            dest_img = yolo_dataset / split / 'images' / img_file.name
            import shutil
            shutil.copy2(img_file, dest_img)
            image_count += 1
        
        print(f"   ✅ {split}: {image_count} images copied")
        print(f"   ⚠️ Note: You need to create annotation files (.txt) in {yolo_dataset / split / 'labels'}/")
        print(f"      Format: class_id center_x center_y width height (normalized 0-1)")
    
    return yolo_dataset

def train_detection_model():
    """Train YOLOv8 object detection model"""
    print("\n🚀 Starting YOLOv8 Object Detection Training...")
    
    # Prepare dataset
    dataset_path = prepare_detection_dataset()
    
    # Create data.yaml
    yaml_path = create_data_yaml()
    
    # Check if annotation files exist
    train_labels = list((dataset_path / 'train' / 'labels').glob('*.txt'))
    val_labels = list((dataset_path / 'val' / 'labels').glob('*.txt'))
    
    if len(train_labels) == 0:
        print("\n⚠️ WARNING: No annotation files found!")
        print("   For object detection, you need bounding box annotations.")
        print("   Run create_annotations.py or manually annotate images using tools like:")
        print("   - LabelImg (https://github.com/tzutalin/labelImg)")
        print("   - Roboflow (https://roboflow.com/)")
        print("   - CVAT (https://cvat.org/)")
        return None, None
    
    print(f"\n   Found {len(train_labels)} train annotations and {len(val_labels)} val annotations")
    
    # Initialize model
    print(f"\n📦 Loading model: {MODEL_TYPE}")
    model = YOLO(MODEL_TYPE)
    
    # Train the model
    print(f"\n🎯 Training Configuration:")
    print(f"   Dataset: {dataset_path}")
    print(f"   Config: {yaml_path}")
    print(f"   Epochs: {EPOCHS}")
    print(f"   Image Size: {IMG_SIZE}")
    print(f"   Batch Size: {BATCH_SIZE}")
    print(f"   Device: {DEVICE}")
    print(f"   Classes: {len(CLASSES)}")
    
    results = model.train(
        data=str(yaml_path),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device=DEVICE,
        project="runs/detect",
        name="fabriq_defect_detection",
        exist_ok=True,
        patience=20,
        save=True,
        plots=True,
        verbose=True
    )
    
    print("\n✅ Training completed!")
    print(f"📊 Results saved in: runs/detect/fabriq_defect_detection/")
    
    return model, results

def validate_model(model):
    """Validate the trained detection model"""
    print("\n🔍 Validating model...")
    
    yaml_path = Path("fabriq_detection_data.yaml")
    results = model.val(data=str(yaml_path))
    
    print("\n📈 Validation Results:")
    print(f"   mAP50: {results.box.map50:.4f}")
    print(f"   mAP50-95: {results.box.map:.4f}")
    
    return results

if __name__ == "__main__":
    print("=" * 60)
    print("FabrIQ Fabric Defect Detection - YOLOv8 Object Detection Training")
    print("=" * 60)
    
    # Train detection model
    model, results = train_detection_model()
    
    if model is not None:
        # Validate
        validate_model(model)
        
        print("\n" + "=" * 60)
        print("🎉 Training Pipeline Complete!")
        print("=" * 60)
        print("\n💡 Next Steps:")
        print("   1. Check results in: runs/detect/fabriq_defect_detection/")
        print("   2. Use the best.pt model for inference with bounding boxes")
        print("   3. Test on new images using inference.py")

