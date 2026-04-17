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

# 1. The 20 Target Classes for your FYP
TARGET_CLASSES = [
    'bad needle line', 'creases', 'double kunda', 'end out', 'fluff knit',
    'fly yarn', 'knit hole', 'lycra short', 'mis pattern', 'mix yarn',
    'normal', 'oil lines', 'oil spot', 'press off', 'pulling thread',
    'run of needle', 'single kunda', 'sinker line', 'tight feeder', 'yarn variation'
]

# 2. The "Smart Mapping" Dictionary
# Maps generic research terms to your specific Industry Terms
CLASS_MAPPING = {
    # --- Exact or Clear Matches ---
    'normal': 'normal', 'good': 'normal', 'defect free': 'normal', 'no defect': 'normal',
    'hole': 'knit hole', 'holes': 'knit hole', 'cut': 'knit hole',
    'oil': 'oil spot', 'stain': 'oil spot', 'dirty': 'oil spot',
    'fuzzyball': 'fluff knit', 'contamination': 'fluff knit',
    'foreign': 'fly yarn', 'fly': 'fly yarn',

    # --- The "Proxy" Matches (Critical for filling specific folders) ---
    # Using 'Vertical Lines' / 'Broken Pick' as proxies for Kunda defects
    'vertical': 'bad needle line',
    'broken pick': 'single kunda',  
    'end out': 'double kunda',      
    
    # Using 'Horizontal Lines' for Sinker/Feeder issues
    'horizontal': 'sinker line',
    'line': 'sinker line',
    'crack': 'tight feeder',
    'thick': 'tight feeder', 

    # Texture issues
    'nep': 'yarn variation',
    'knot': 'yarn variation',
    'variation': 'yarn variation',
    'crease': 'creases',
    'wrinkle': 'creases',
    
    # Knitting Structure Errors
    'selvage': 'press off',
    'pattern': 'mis pattern',
    'mispattern': 'mis pattern',
    'thread': 'pulling thread',
    'pulling': 'pulling thread',
    'broken end': 'run of needle',
    'needle': 'run of needle',
    'weft': 'lycra short',         
    'color': 'mix yarn',
}

def normalize_name(name):
    """Cleans up folder names for easier matching."""
    return name.lower().strip().replace('_', ' ').replace('-', ' ')

def find_target_class(folder_name, file_name, full_path):
    """Decides which FabrIQ class an image belongs to."""
    # Convert everything to lowercase for matching
    search_terms = normalize_name(folder_name).split() + normalize_name(file_name).split()
    path_str = str(full_path).lower()

    # Priority 1: Check if path contains "normal" or "good"
    if any(x in path_str for x in ['nodefect', 'no defect', 'defect free', 'good']):
        return 'normal'

    # Priority 2: Check our Mapping Dictionary
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

    # Priority 3: Default Fail-safe
    # If we find a generic "defect" folder but don't know which, put it in 'mix yarn'
    # so we don't lose data.
    if 'defect' in path_str:
        return 'mix yarn'
        
    return None # Skip this file if we can't identify it

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