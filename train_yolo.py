"""
YOLOv8 Training Script for FabrIQ Fabric Defect Detection
Supports both Classification and Object Detection modes
"""

import os
from pathlib import Path
from ultralytics import YOLO
import yaml

# Configuration
DATASET_PATH = Path("FabrIQ_Final_Dataset")
MODEL_TYPE = "yolov8n-cls.pt"  # Classification model (use yolov8n.pt for detection)
EPOCHS = 50  # Reduced for CPU training
IMG_SIZE = 224  # Smaller size for CPU (640 is too large for CPU)
BATCH_SIZE = 4  # Smaller batch for CPU (adjust based on RAM)
# Auto-detect device (will use CPU if no GPU)
try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except:
    DEVICE = "cpu"

# 20 Target Classes
CLASSES = [
    'bad needle line', 'creases', 'double kunda', 'end out', 'fluff knit',
    'fly yarn', 'knit hole', 'lycra short', 'mis pattern', 'mix yarn',
    'normal', 'oil lines', 'oil spot', 'press off', 'pulling thread',
    'run of needle', 'single kunda', 'sinker line', 'tight feeder', 'yarn variation'
]

def prepare_classification_dataset():
    """Prepare dataset structure for YOLO classification"""
    print("📁 Preparing dataset structure for YOLO classification...")
    
    # YOLO classification expects: dataset/train/class1, dataset/train/class2, etc.
    yolo_dataset = Path("FabrIQ_YOLO_Dataset")
    
    for split in ['train', 'val']:
        source_dir = DATASET_PATH / split / 'images'
        
        if not source_dir.exists():
            print(f"⚠️ Warning: {source_dir} does not exist!")
            continue
        
        # Create class folders
        for class_name in CLASSES:
            class_folder = yolo_dataset / split / class_name.replace(' ', '_')
            class_folder.mkdir(parents=True, exist_ok=True)
        
        # Move images to class folders based on filename
        print(f"   Processing {split} images...")
        image_count = 0
        
        for img_file in source_dir.glob("*.jpg"):
            # Extract class from filename: FabrIQ_class_name_00001.jpg
            filename = img_file.stem  # Without extension
            parts = filename.split('_')
            
            if len(parts) >= 2 and parts[0] == 'FabrIQ':
                # Reconstruct class name (handle multi-word classes)
                class_parts = parts[1:-1]  # Everything except 'FabrIQ' and the index
                class_name = '_'.join(class_parts)
                
                # Map back to original class name with spaces
                class_name_with_spaces = class_name.replace('_', ' ')
                
                if class_name_with_spaces in CLASSES:
                    dest_folder = yolo_dataset / split / class_name
                    dest_file = dest_folder / img_file.name
                    
                    # Copy file
                    import shutil
                    shutil.copy2(img_file, dest_file)
                    image_count += 1
        
        print(f"   ✅ {split}: {image_count} images organized")
    
    return yolo_dataset

def train_classification_model():
    """Train YOLOv8 classification model"""
    print("\n🚀 Starting YOLOv8 Classification Training...")
    
    # Prepare dataset
    dataset_path = prepare_classification_dataset()
    
    # Verify dataset structure
    train_folders = [d for d in (dataset_path / 'train').iterdir() if d.is_dir()]
    if len(train_folders) == 0:
        print("❌ Error: No class folders found in dataset!")
        print("   Please check your dataset structure.")
        return None, None
    
    print(f"   Found {len(train_folders)} class folders")
    
    # Initialize model
    print(f"\n📦 Loading model: {MODEL_TYPE}")
    model = YOLO(MODEL_TYPE)
    
    # Train the model
    print(f"\n🎯 Training Configuration:")
    print(f"   Dataset: {dataset_path}")
    print(f"   Epochs: {EPOCHS}")
    print(f"   Image Size: {IMG_SIZE}")
    print(f"   Batch Size: {BATCH_SIZE}")
    print(f"   Device: {DEVICE}")
    if DEVICE == "cpu":
        print(f"   ⚠️  Using CPU - Training will be slower. Consider reducing epochs or batch size.")
    print(f"   Classes: {len(CLASSES)}")
    
    results = model.train(
        data=str(dataset_path),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device=DEVICE,
        project="runs/classify",
        name="fabriq_defect_classification",
        exist_ok=True,
        patience=20,  # Early stopping patience
        save=True,
        plots=True,
        verbose=True
    )
    
    print("\n✅ Training completed!")
    print(f"📊 Results saved in: runs/classify/fabriq_defect_classification/")
    
    return model, results

def validate_model(model):
    """Validate the trained model"""
    print("\n🔍 Validating model...")
    
    dataset_path = Path("FabrIQ_YOLO_Dataset")
    results = model.val(data=str(dataset_path))
    
    print("\n📈 Validation Results:")
    print(f"   Top-1 Accuracy: {results.top1:.4f}")
    print(f"   Top-5 Accuracy: {results.top5:.4f}")
    
    return results

def export_model(model):
    """Export model to different formats"""
    print("\n📤 Exporting model...")
    
    # Export to ONNX
    try:
        model.export(format='onnx')
        print("   ✅ ONNX format exported")
    except Exception as e:
        print(f"   ⚠️ ONNX export failed: {e}")
    
    # Export to TensorRT (if available)
    try:
        model.export(format='engine')
        print("   ✅ TensorRT format exported")
    except Exception as e:
        print(f"   ⚠️ TensorRT export failed: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("FabrIQ Fabric Defect Detection - YOLOv8 Training")
    print("=" * 60)
    
    # Train classification model
    model, results = train_classification_model()
    
    # Validate
    validate_model(model)
    
    # Export
    export_model(model)
    
    print("\n" + "=" * 60)
    print("🎉 Training Pipeline Complete!")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("   1. Check results in: runs/classify/fabriq_defect_classification/")
    print("   2. Use the best.pt model for inference")
    print("   3. For object detection with bounding boxes, use prepare_detection_dataset.py")

