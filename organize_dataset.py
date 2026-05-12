import os
import shutil
from pathlib import Path
import random
from collections import defaultdict
import time

# --- CONFIGURATION ---
OUTPUT_FOLDER_NAME = 'FabrIQ_Final_Dataset'
TRAIN_RATIO = 0.8  # 80% Train, 20% Validation
SEED = 42          # For reproducible results

# 1. Seven target defect classes (slug form; used in FabrIQ_<slug>_<idx>.jpg)
TARGET_CLASSES = [
    'contamination',
    'selvet',
    'gray_stitch',
    'cut',
    'baekra',
    'color_issue',
    'stain',
]

# 2. Map folder / filename keywords → target slug (longer keys matched first)
CLASS_MAPPING = {
    'contamination': 'contamination',
    'contaminant': 'contamination',
    'dirt': 'contamination',
    'foreign': 'contamination',
    'selvet': 'selvet',
    'selvedge': 'selvet',
    'selvage': 'selvet',
    'gray stitch': 'gray_stitch',
    'graystitch': 'gray_stitch',
    'gray_stitch': 'gray_stitch',
    'stitch': 'gray_stitch',
    'cut': 'cut',
    'tear': 'cut',
    'hole': 'cut',
    'baekra': 'baekra',
    'bakra': 'baekra',
    'color issue': 'color_issue',
    'color issues': 'color_issue',
    'color_issue': 'color_issue',
    'shade': 'color_issue',
    'shading': 'color_issue',
    'wrong color': 'color_issue',
    'stain': 'stain',
    'oil': 'stain',
    'spot': 'stain',
    'dirty': 'stain',
}

def normalize_name(name):
    """Cleans up folder names for easier matching."""
    return name.lower().strip().replace('_', ' ').replace('-', ' ')

def find_target_class(folder_name, file_name, full_path):
    """Decides which FabrIQ class an image belongs to."""
    path_str = str(full_path).lower()
    folder_slug = normalize_name(folder_name).replace(' ', '_')

    # Priority 0: Folder name is already a target slug
    if folder_slug in TARGET_CLASSES:
        return folder_slug
    for cls in TARGET_CLASSES:
        if cls.replace('_', ' ') == normalize_name(folder_name):
            return cls

    # Skip clearly non-defect samples (optional)
    if any(x in path_str for x in ['nodefect', 'no defect', 'defect free', 'good', 'normal']):
        return None

    # Priority 1: Check our Mapping Dictionary
    # We check longer keys first (e.g., match 'oil spot' before 'oil')
    sorted_keys = sorted(CLASS_MAPPING.keys(), key=len, reverse=True)
    
    # Check folder name first (strongest signal)
    f_name_norm = normalize_name(folder_name)
    for key in sorted_keys:
        if key in f_name_norm:
            return CLASS_MAPPING[key]

    # Check filename second
    f_file_norm = normalize_name(file_name)
    for key in sorted_keys:
        if key in f_file_norm:
            return CLASS_MAPPING[key]

    return None

def organize():
    print(f"🚀 Starting FabrIQ Data Pipeline...")
    random.seed(SEED)
    
    # Setup Paths
    root_dir = Path.cwd()
    output_dir = root_dir / OUTPUT_FOLDER_NAME
    
    # Create Output Structure
    for split in ['train', 'val']:
        (output_dir / split / 'images').mkdir(parents=True, exist_ok=True)
    
    # Scan for Images
    print("   Scanning folders for raw images...")
    valid_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}
    found_files = defaultdict(list)
    
    for path in root_dir.rglob('*'):
        # Skip our own output folder
        if OUTPUT_FOLDER_NAME in str(path):
            continue
            
        if path.is_file() and path.suffix.lower() in valid_exts:
            # Determine Class
            target = find_target_class(path.parent.name, path.name, path)
            if target:
                found_files[target].append(path)

    # Check for empty classes
    print("\n📊 Data Distribution Analysis:")
    total_processed = 0
    
    for cls in TARGET_CLASSES:
        count = len(found_files[cls])
        status = "✅" if count > 0 else "⚠️ EMPTY"
        print(f"   {status} {cls.ljust(20)}: {count} images found")

    print("\n   Processing and Copying Files...")
    
    # Process Files
    for cls in TARGET_CLASSES:
        images = found_files[cls]
        random.shuffle(images)
        
        # Split Index
        split_idx = int(len(images) * TRAIN_RATIO)
        splits = {
            'train': images[:split_idx],
            'val': images[split_idx:]
        }
        
        for split_name, split_imgs in splits.items():
            for idx, img_path in enumerate(split_imgs):
                # New Name: FabrIQ_single_kunda_00123.jpg
                clean_cls_name = cls.replace(' ', '_')
                new_name = f"FabrIQ_{clean_cls_name}_{idx+1:05d}{img_path.suffix}"
                
                dest = output_dir / split_name / 'images' / new_name
                
                try:
                    shutil.copy2(img_path, dest)
                    total_processed += 1
                except Exception as e:
                    print(f"Error copying {img_path}: {e}")

    print(f"\n🎉 SUCCESS! processed {total_processed} images.")
    print(f"📂 Dataset Ready at: {output_dir}")
    print("   (Take a screenshot of this folder structure for your presentation!)")

if __name__ == "__main__":
    organize()