"""
Create Pseudo-Annotations for YOLO Detection
This script creates full-image bounding boxes for classification dataset
Useful when you don't have manual annotations but want to train detection model
"""

from pathlib import Path
import shutil

DATASET_PATH = Path("FabrIQ_Final_Dataset")
OUTPUT_PATH = Path("FabrIQ_YOLO_Detection_Dataset")

# 7 defect classes (must match organize_dataset / fabriq_detection_data.yaml)
CLASSES = [
    'contamination',
    'selvet',
    'gray_stitch',
    'cut',
    'baekra',
    'color_issue',
    'stain',
]

def create_full_image_annotation(image_path, class_name):
    """
    Create a YOLO annotation file with full-image bounding box
    Format: class_id center_x center_y width height
    Full image box: 0.5 0.5 1.0 1.0 (centered, full size)
    """
    if class_name not in CLASSES:
        return None
    
    class_id = CLASSES.index(class_name)
    
    # Full image bounding box (normalized)
    # center_x = 0.5, center_y = 0.5, width = 1.0, height = 1.0
    annotation = f"{class_id} 0.5 0.5 1.0 1.0\n"
    
    return annotation

def create_annotations():
    """Create pseudo-annotations for all images"""
    print("📝 Creating pseudo-annotations (full-image bounding boxes)...")
    print("⚠️  Note: These are pseudo-annotations. For better results, use manual annotations.")
    
    # Create output structure
    for split in ['train', 'val']:
        (OUTPUT_PATH / split / 'images').mkdir(parents=True, exist_ok=True)
        (OUTPUT_PATH / split / 'labels').mkdir(parents=True, exist_ok=True)
    
    total_annotations = 0
    
    for split in ['train', 'val']:
        source_dir = DATASET_PATH / split / 'images'
        
        if not source_dir.exists():
            print(f"⚠️  Warning: {source_dir} does not exist!")
            continue
        
        print(f"\n   Processing {split} images...")
        count = 0
        
        for img_file in source_dir.glob("*.jpg"):
            # Extract class from filename: FabrIQ_class_name_00001.jpg
            filename = img_file.stem
            parts = filename.split('_')
            
            if len(parts) >= 2 and parts[0] == 'FabrIQ':
                # Reconstruct class name
                class_parts = parts[1:-1]
                class_name = '_'.join(class_parts)
                class_slug = class_name  # filename uses underscores, e.g. gray_stitch
                if class_slug in CLASSES:
                    # Copy image
                    dest_img = OUTPUT_PATH / split / 'images' / img_file.name
                    shutil.copy2(img_file, dest_img)
                    
                    # Create annotation
                    annotation = create_full_image_annotation(img_file, class_slug)
                    if annotation:
                        label_file = OUTPUT_PATH / split / 'labels' / f"{img_file.stem}.txt"
                        with open(label_file, 'w') as f:
                            f.write(annotation)
                        count += 1
                        total_annotations += 1
        
        print(f"   ✅ {split}: {count} annotations created")
    
    print(f"\n✅ Total annotations created: {total_annotations}")
    print(f"📁 Dataset ready at: {OUTPUT_PATH}")
    print("\n💡 Next Steps:")
    print("   1. Review annotations in labels/ folders")
    print("   2. For better results, manually annotate using LabelImg or Roboflow")
    print("   3. Run: python train_yolo_detection.py")

if __name__ == "__main__":
    create_annotations()

