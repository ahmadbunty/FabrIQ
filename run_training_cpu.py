"""
CPU-Optimized Training Script for FabrIQ Fabric Defect Detection
Optimized settings for CPU-only training (slower but works without GPU)
"""

import os
from pathlib import Path
from ultralytics import YOLO
import torch

print("=" * 60)
print("FabrIQ YOLO Training - CPU Mode")
print("=" * 60)

# Check device
if torch.cuda.is_available():
    print("✅ GPU detected! Using GPU for faster training.")
    print("   If you want to force CPU, set: DEVICE = 'cpu'")
    DEVICE = "cuda"
else:
    print("⚠️  No GPU detected. Using CPU (training will be slower).")
    print("   Estimated time: 2-6 hours depending on dataset size.")
    DEVICE = "cpu"

# CPU-Optimized Configuration
DATASET_PATH = Path("FabrIQ_Final_Dataset")
MODEL_TYPE = "yolov8n-cls.pt"  # Nano model (smallest, fastest)

# CPU-friendly settings
if DEVICE == "cpu":
    EPOCHS = 30  # Fewer epochs for CPU
    IMG_SIZE = 224  # Smaller image size (faster on CPU)
    BATCH_SIZE = 4  # Small batch size (adjust if you get memory errors)
    WORKERS = 2  # Number of CPU workers
    print("\n📊 CPU-Optimized Settings:")
    print(f"   Epochs: {EPOCHS} (reduced for faster training)")
    print(f"   Image Size: {IMG_SIZE} (smaller = faster)")
    print(f"   Batch Size: {BATCH_SIZE} (reduce to 2 if out of memory)")
    print(f"   Workers: {WORKERS}")
else:
    EPOCHS = 50
    IMG_SIZE = 224
    BATCH_SIZE = 16
    WORKERS = 4

# 7 defect classes (slugs)
CLASSES = [
    'contamination',
    'selvet',
    'gray_stitch',
    'cut',
    'baekra',
    'color_issue',
    'stain',
]

def prepare_classification_dataset():
    """Prepare dataset structure for YOLO classification"""
    print("\n📁 Preparing dataset structure...")
    
    yolo_dataset = Path("FabrIQ_YOLO_Dataset")
    
    for split in ['train', 'val']:
        source_dir = DATASET_PATH / split / 'images'
        
        if not source_dir.exists():
            print(f"⚠️  Warning: {source_dir} does not exist!")
            print("   Make sure you've run organize_dataset.py first!")
            return None
        
        # Create class folders
        for class_name in CLASSES:
            class_folder = yolo_dataset / split / class_name.replace(' ', '_')
            class_folder.mkdir(parents=True, exist_ok=True)
        
        # Move images to class folders based on filename
        print(f"   Processing {split} images...")
        image_count = 0
        
        for img_file in source_dir.glob("*.jpg"):
            filename = img_file.stem
            parts = filename.split('_')
            
            if len(parts) >= 2 and parts[0] == 'FabrIQ':
                class_parts = parts[1:-1]
                class_name = '_'.join(class_parts)
                if class_name in CLASSES:
                    dest_folder = yolo_dataset / split / class_name.replace(' ', '_')
                    dest_file = dest_folder / img_file.name
                    
                    import shutil
                    shutil.copy2(img_file, dest_file)
                    image_count += 1
        
        print(f"   ✅ {split}: {image_count} images organized")
    
    return yolo_dataset

def train_model():
    """Train YOLOv8 classification model"""
    print("\n🚀 Starting Training...")
    
    # Prepare dataset
    dataset_path = prepare_classification_dataset()
    
    if dataset_path is None:
        print("\n❌ Dataset preparation failed!")
        return
    
    # Verify dataset
    train_folders = [d for d in (dataset_path / 'train').iterdir() if d.is_dir()]
    if len(train_folders) == 0:
        print("❌ Error: No class folders found!")
        return
    
    print(f"   Found {len(train_folders)} class folders")
    
    # Initialize model
    print(f"\n📦 Loading model: {MODEL_TYPE}")
    model = YOLO(MODEL_TYPE)
    
    # Train
    print(f"\n🎯 Starting training...")
    print(f"   This may take a while on CPU. Please be patient!")
    print(f"   You can monitor progress in: runs/classify/fabriq_defect_classification/")
    
    try:
        results = model.train(
            data=str(dataset_path),
            epochs=EPOCHS,
            imgsz=IMG_SIZE,
            batch=BATCH_SIZE,
            device=DEVICE,
            workers=WORKERS,
            project="runs/classify",
            name="fabriq_defect_classification",
            exist_ok=True,
            patience=10,  # Early stopping
            save=True,
            plots=True,
            verbose=True
        )
        
        print("\n✅ Training completed!")
        print(f"📊 Results saved in: runs/classify/fabriq_defect_classification/")
        print(f"📁 Best model: runs/classify/fabriq_defect_classification/weights/best.pt")
        
        # Validate
        print("\n🔍 Validating model...")
        val_results = model.val(data=str(dataset_path))
        print(f"\n📈 Validation Results:")
        print(f"   Top-1 Accuracy: {val_results.top1:.4f}")
        print(f"   Top-5 Accuracy: {val_results.top5:.4f}")
        
        return model, results
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Reduce BATCH_SIZE to 2 if out of memory")
        print("   2. Reduce IMG_SIZE to 128 if still having issues")
        print("   3. Make sure dataset is properly organized")
        return None, None

if __name__ == "__main__":
    # Check if dataset exists
    if not DATASET_PATH.exists():
        print("\n❌ Error: FabrIQ_Final_Dataset not found!")
        print("\n📝 Steps to prepare:")
        print("   1. Make sure your Dataset/Dataset folder has class folders")
        print("   2. Run: python organize_dataset.py")
        print("   3. Then run this script again")
        exit(1)
    
    # Start training
    model, results = train_model()
    
    if model is not None:
        print("\n" + "=" * 60)
        print("🎉 Training Complete!")
        print("=" * 60)
        print("\n💡 Next Steps:")
        print("   1. Check results: runs/classify/fabriq_defect_classification/")
        print("   2. Test model: python inference.py --model runs/classify/fabriq_defect_classification/weights/best.pt --source path/to/image.jpg")
        print("   3. View training plots: runs/classify/fabriq_defect_classification/results.png")

