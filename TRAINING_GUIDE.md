# 🚀 FabrIQ YOLO Training - Complete Guide

## Overview

This training pipeline provides two modes for fabric defect detection:

1. **Classification Mode**: Classifies entire images into 20 defect categories
2. **Detection Mode**: Detects defects with bounding boxes (requires annotations)

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## 🎯 Quick Start

### Option 1: Interactive Quick Start
```bash
python quick_start.py
```

### Option 2: Direct Training

**For Classification:**
```bash
python train_yolo.py
```

**For Detection (with bounding boxes):**
```bash
# First, create annotations (if needed)
python create_pseudo_annotations.py

# Then train
python train_yolo_detection.py
```

## 📊 Dataset Structure

Your dataset should be organized as:
```
FabrIQ_Final_Dataset/
├── train/
│   └── images/
│       ├── FabrIQ_normal_00001.jpg
│       ├── FabrIQ_knit_hole_00001.jpg
│       └── ...
└── val/
    └── images/
        ├── FabrIQ_normal_00001.jpg
        └── ...
```

## 🎓 Training Modes Explained

### 1. Classification Mode (`train_yolo.py`)

**What it does:**
- Classifies entire images into one of 20 defect classes
- No bounding boxes needed
- Faster training and inference

**Best for:**
- Image-level defect classification
- Quality control systems
- Batch processing of fabric images

**Output:**
- Model predicts: "This image contains a knit hole"
- Confidence scores for all 20 classes

### 2. Detection Mode (`train_yolo_detection.py`)

**What it does:**
- Detects defects with bounding boxes
- Provides spatial location of defects
- Can detect multiple defects per image

**Best for:**
- Locating defects in large images
- Quality inspection with defect location
- Detailed defect analysis

**Output:**
- Model predicts: "Knit hole at coordinates (x1, y1) to (x2, y2)"
- Multiple detections possible per image

## 📝 Creating Annotations for Detection

### Method 1: Pseudo-Annotations (Quick Start)
```bash
python create_pseudo_annotations.py
```
Creates full-image bounding boxes. Good for initial testing.

### Method 2: Manual Annotation (Recommended)

**Using LabelImg:**
```bash
pip install labelImg
labelImg
```

Steps:
1. Open `FabrIQ_YOLO_Detection_Dataset/train/images/`
2. Draw bounding boxes around defects
3. Select class from dropdown
4. Save in YOLO format
5. Repeat for all images

**Annotation Format:**
```
class_id center_x center_y width height
```

Example:
```
7 0.5 0.5 0.3 0.4
```
- Class 7 = "knit hole"
- Center at (0.5, 0.5) = middle of image
- Size: 30% width, 40% height

## 🔧 Configuration

Edit training parameters in the scripts:

```python
EPOCHS = 100          # Training epochs
IMG_SIZE = 640        # Image size (640, 1280, etc.)
BATCH_SIZE = 16       # Batch size (adjust for GPU memory)
MODEL_TYPE = "yolov8n-cls.pt"  # Model size
```

**Model Sizes:**
- `yolov8n`: Nano (fastest, smallest)
- `yolov8s`: Small
- `yolov8m`: Medium
- `yolov8l`: Large
- `yolov8x`: Extra Large (best accuracy, slowest)

## 🔍 Inference

### Classification:
```bash
python inference.py \
    --model runs/classify/fabriq_defect_classification/weights/best.pt \
    --source path/to/image.jpg \
    --mode classification \
    --save
```

### Detection:
```bash
python inference.py \
    --model runs/detect/fabriq_defect_detection/weights/best.pt \
    --source path/to/image.jpg \
    --mode detection \
    --conf 0.25 \
    --save
```

### Batch Processing:
```bash
python inference.py \
    --model runs/classify/fabriq_defect_classification/weights/best.pt \
    --source path/to/folder/ \
    --mode classification \
    --save \
    --output results/
```

## 📈 Monitoring Training

Training progress is saved in:
- **Classification**: `runs/classify/fabriq_defect_classification/`
- **Detection**: `runs/detect/fabriq_defect_detection/`

Key files:
- `results.png`: Training curves (loss, accuracy)
- `confusion_matrix.png`: Classification accuracy matrix
- `best.pt`: Best model weights
- `last.pt`: Latest model weights

## 🎯 20 Defect Classes

1. bad needle line
2. creases
3. double kunda
4. end out
5. fluff knit
6. fly yarn
7. knit hole
8. lycra short
9. mis pattern
10. mix yarn
11. normal
12. oil lines
13. oil spot
14. press off
15. pulling thread
16. run of needle
17. single kunda
18. sinker line
19. tight feeder
20. yarn variation

## 🐛 Troubleshooting

### Out of Memory (OOM)
- Reduce `BATCH_SIZE` (try 8 or 4)
- Reduce `IMG_SIZE` (try 416 instead of 640)
- Use smaller model (`yolov8n` instead of `yolov8x`)

### Poor Accuracy
- Check dataset balance (some classes may have too few images)
- Increase training epochs
- Try data augmentation
- Use larger model
- Ensure correct class labels

### Slow Training
- Use GPU (CUDA)
- Reduce image size
- Reduce batch size
- Use smaller model

### No Annotations Found
- For detection, ensure `.txt` files exist in `labels/` folder
- Check annotation format matches YOLO standard
- Verify class IDs are 0-19

## 📚 Additional Resources

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Ultralytics GitHub](https://github.com/ultralytics/ultralytics)
- [LabelImg Tool](https://github.com/tzutalin/labelImg)

## ✅ Training Checklist

- [ ] Dataset organized in `FabrIQ_Final_Dataset/`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] GPU available (optional but recommended)
- [ ] Choose training mode (classification or detection)
- [ ] For detection: annotations created
- [ ] Training script configured
- [ ] Training started
- [ ] Results checked in `runs/` folder
- [ ] Model tested on validation set
- [ ] Inference script tested

## 🎉 Next Steps After Training

1. **Evaluate Model**: Check validation results
2. **Test on New Images**: Use inference script
3. **Fine-tune**: Adjust hyperparameters if needed
4. **Deploy**: Integrate into production system
5. **Monitor**: Track performance on real data

---

**Happy Training! 🚀**

