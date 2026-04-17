"""
Quick Start Script for FabrIQ YOLO Training
This script guides you through the training process
"""

import sys
from pathlib import Path

def check_dataset():
    """Check if dataset exists"""
    dataset_path = Path("FabrIQ_Final_Dataset")
    
    if not dataset_path.exists():
        print("❌ Error: FabrIQ_Final_Dataset not found!")
        print("   Please run organize_dataset.py first to create the dataset.")
        return False
    
    train_images = list((dataset_path / "train" / "images").glob("*.jpg"))
    val_images = list((dataset_path / "val" / "images").glob("*.jpg"))
    
    print(f"✅ Dataset found:")
    print(f"   Train images: {len(train_images)}")
    print(f"   Val images: {len(val_images)}")
    
    if len(train_images) == 0:
        print("⚠️  Warning: No training images found!")
        return False
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n🔍 Checking dependencies...")
    
    try:
        import ultralytics
        print("   ✅ ultralytics installed")
    except ImportError:
        print("   ❌ ultralytics not installed")
        print("   Run: pip install -r requirements.txt")
        return False
    
    try:
        import torch
        print(f"   ✅ PyTorch installed (version: {torch.__version__})")
        
        # Check for CUDA
        if torch.cuda.is_available():
            print(f"   ✅ CUDA available (GPU: {torch.cuda.get_device_name(0)})")
        else:
            print("   ⚠️  CUDA not available (will use CPU - slower)")
    except ImportError:
        print("   ❌ PyTorch not installed")
        return False
    
    return True

def main():
    print("=" * 60)
    print("FabrIQ YOLO Training - Quick Start")
    print("=" * 60)
    
    # Check dataset
    if not check_dataset():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Choose Training Mode:")
    print("=" * 60)
    print("1. Classification (Image-level classification)")
    print("   - No bounding boxes needed")
    print("   - Faster to train")
    print("   - Good for defect classification")
    print()
    print("2. Object Detection (Bounding box detection)")
    print("   - Requires bounding box annotations")
    print("   - More complex but provides spatial info")
    print("   - Good for locating defects in images")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting Classification Training...")
        print("   Run: python train_yolo.py")
        import train_yolo
        train_yolo.train_classification_model()
    elif choice == "2":
        print("\n🚀 Starting Detection Training...")
        print("   Note: You need bounding box annotations (.txt files)")
        print("   If you don't have annotations, run: python create_pseudo_annotations.py")
        
        # Check for annotations
        detection_dataset = Path("FabrIQ_YOLO_Detection_Dataset")
        if detection_dataset.exists():
            train_labels = list((detection_dataset / "train" / "labels").glob("*.txt"))
            if len(train_labels) > 0:
                print(f"   ✅ Found {len(train_labels)} annotation files")
                import train_yolo_detection
                train_yolo_detection.train_detection_model()
            else:
                print("   ⚠️  No annotation files found!")
                print("   Run: python create_pseudo_annotations.py")
                print("   Or manually annotate using LabelImg")
        else:
            print("   ⚠️  Detection dataset not prepared!")
            print("   Run: python create_pseudo_annotations.py")
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    main()

