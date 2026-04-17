# FabrIQ Fabric Defect Detection - YOLO Training Guide

This guide explains how to train YOLOv8 models for fabric defect detection and classification.

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **CUDA-capable GPU** (recommended for faster training)
3. **Organized dataset** in `FabrIQ_Final_Dataset/` folder

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Choose Training Mode

#### Option A: Classification (Image-Level Classification)
- **Use Case**: Classify entire images into defect categories
- **No bounding boxes required**
- **Faster to train, easier to use**

```bash
python train_yolo.py
```

#### Option B: Object Detection (Bounding Box Detection)
- **Use Case**: Detect and locate defects with bounding boxes
- **Requires bounding box annotations**
- **More complex but provides spatial information**

```bash
python train_yolo_detection.py
```

## 📁 Dataset Structure

### For Classification:
```
FabrIQ_YOLO_Dataset/
├── train/
│   ├── bad_needle_line/
│   ├── creases/
│   ├── double_kunda/
│   └── ... (20 class folders)
└── val/
    ├── bad_needle_line/
    ├── creases/
    └── ... (20 class folders)
```

### For Detection:
```
FabrIQ_YOLO_Detection_Dataset/
├── train/
│   ├── images/
│   └── labels/  (YOLO format .txt files)
└── val/
    ├── images/
    └── labels/  (YOLO format .txt files)
```

## 🎯 YOLO Annotation Format (for Detection)

Each image needs a corresponding `.txt` file with bounding boxes:

```
class_id center_x center_y width height
```

Example (`image.jpg` → `image.txt`):
```
0 0.5 0.5 0.3 0.4
2 0.2 0.3 0.1 0.2
```

Where:
- `class_id`: Index of class (0-19)
- `center_x, center_y`: Center coordinates (normalized 0-1)
- `width, height`: Box dimensions (normalized 0-1)

## 🔧 Training Configuration

Edit the training scripts to adjust:

- **EPOCHS**: Number of training epochs (default: 100)
- **IMG_SIZE**: Input image size (default: 640)
- **BATCH_SIZE**: Batch size (adjust based on GPU memory)
- **MODEL_TYPE**: 
  - Classification: `yolov8n-cls.pt`, `yolov8s-cls.pt`, `yolov8m-cls.pt`
  - Detection: `yolov8n.pt`, `yolov8s.pt`, `yolov8m.pt`, `yolov8l.pt`, `yolov8x.pt`

## 📊 Training Results

After training, check:

- **Classification**: `runs/classify/fabriq_defect_classification/`
- **Detection**: `runs/detect/fabriq_defect_detection/`

Key files:
- `best.pt`: Best model weights
- `results.png`: Training curves
- `confusion_matrix.png`: Classification matrix

## 🔍 Inference

### Classification Mode:
```bash
python inference.py --model runs/classify/fabriq_defect_classification/weights/best.pt \
                    --source path/to/image.jpg \
                    --mode classification \
                    --save
```

### Detection Mode:
```bash
python inference.py --model runs/detect/fabriq_defect_detection/weights/best.pt \
                    --source path/to/image.jpg \
                    --mode detection \
                    --conf 0.25 \
                    --save
```

## 📝 Creating Bounding Box Annotations

If you need to create annotations for detection:

1. **Use LabelImg** (Recommended):
   ```bash
   pip install labelImg
   labelImg
   ```
   - Open image directory
   - Draw bounding boxes
   - Save in YOLO format

2. **Use Roboflow** (Online):
   - Upload images to https://roboflow.com/
   - Annotate online
   - Export in YOLO format

3. **Use CVAT** (Advanced):
   - Install CVAT for team annotation
   - Export in YOLO format

## 🎓 Model Performance Tips

1. **Data Augmentation**: YOLOv8 includes automatic augmentation
2. **Transfer Learning**: Models are pre-trained on COCO dataset
3. **Early Stopping**: Configured with patience=20
4. **Image Size**: Larger sizes (1280) improve accuracy but slower
5. **Batch Size**: Increase if you have more GPU memory

## 🐛 Troubleshooting

### Out of Memory Error:
- Reduce `BATCH_SIZE`
- Reduce `IMG_SIZE`
- Use smaller model (yolov8n instead of yolov8x)

### Poor Accuracy:
- Check dataset balance
- Increase training epochs
- Use data augmentation
- Try larger model

### No Annotations Found:
- For detection, ensure `.txt` files exist in `labels/` folder
- Check annotation format matches YOLO standard

## 📚 Additional Resources

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Ultralytics GitHub](https://github.com/ultralytics/ultralytics)
- [YOLO Format Guide](https://roboflow.com/formats/yolo-annotation-format)

## 🎉 Next Steps

1. Train your model
2. Evaluate on validation set
3. Test on new images
4. Deploy for production use

