# 🚀 How to Run FabrIQ YOLO Training (CPU/GPU Guide)

## Quick Answer

**GPU is NOT required**, but training will be **much slower on CPU** (2-6 hours vs 30-60 minutes).

## 📋 Step-by-Step Instructions

### Step 1: Install Dependencies

Open terminal/command prompt in the project folder and run:

```bash
pip install -r requirements.txt
```

**Note**: This will install PyTorch. If you have issues, install PyTorch separately:
- **CPU only**: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`
- **With GPU (CUDA)**: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118`

### Step 2: Prepare Your Dataset

Make sure your dataset is organized. If you haven't already:

```bash
python organize_dataset.py
```

This creates `FabrIQ_Final_Dataset/` with train/val splits.

### Step 3: Run Training

#### Option A: CPU-Optimized Script (Recommended for CPU)

```bash
python run_training_cpu.py
```

This script:
- ✅ Automatically detects CPU/GPU
- ✅ Uses optimized settings for CPU
- ✅ Smaller batch size and image size
- ✅ Fewer epochs for faster training

#### Option B: Standard Training Script

```bash
python train_yolo.py
```

**Note**: Edit the script first to reduce settings if using CPU:
- `BATCH_SIZE = 4` (or 2)
- `IMG_SIZE = 224` (instead of 640)
- `EPOCHS = 30` (instead of 100)

### Step 4: Wait for Training

**CPU Training Time:**
- Small dataset (< 1000 images): 1-2 hours
- Medium dataset (1000-10000 images): 2-4 hours
- Large dataset (> 10000 images): 4-8 hours

**GPU Training Time:**
- Small dataset: 10-20 minutes
- Medium dataset: 20-40 minutes
- Large dataset: 40-60 minutes

You'll see progress updates in the terminal.

### Step 5: Check Results

After training completes, check:

```
runs/classify/fabriq_defect_classification/
├── weights/
│   ├── best.pt          ← Your trained model!
│   └── last.pt
├── results.png          ← Training curves
└── confusion_matrix.png ← Accuracy matrix
```

## 🔧 CPU vs GPU Comparison

| Feature | CPU | GPU |
|---------|-----|-----|
| **Speed** | Slow (2-6 hours) | Fast (30-60 min) |
| **Memory** | Uses RAM | Uses VRAM |
| **Batch Size** | 2-4 | 16-32 |
| **Image Size** | 224-416 | 640-1280 |
| **Cost** | Free (you have it) | Requires GPU |
| **Setup** | Easy | Need CUDA |

## ⚙️ CPU Optimization Tips

If training is too slow on CPU:

1. **Reduce Batch Size**:
   ```python
   BATCH_SIZE = 2  # In the script
   ```

2. **Reduce Image Size**:
   ```python
   IMG_SIZE = 128  # Smaller = faster
   ```

3. **Reduce Epochs**:
   ```python
   EPOCHS = 20  # Fewer epochs
   ```

4. **Use Smaller Model**:
   ```python
   MODEL_TYPE = "yolov8n-cls.pt"  # Nano (smallest)
   ```

5. **Reduce Dataset Size** (for testing):
   - Use only a subset of images for initial testing

## 🐛 Common Issues

### Issue: "Out of Memory" Error

**Solution:**
- Reduce `BATCH_SIZE` to 2 or 1
- Reduce `IMG_SIZE` to 128
- Close other applications

### Issue: Training Too Slow

**Solution:**
- Use `run_training_cpu.py` (optimized for CPU)
- Reduce epochs to 20-30
- Use smaller image size (224)
- Consider using Google Colab (free GPU)

### Issue: "CUDA out of memory" (on GPU)

**Solution:**
- Reduce `BATCH_SIZE` to 8 or 4
- Reduce `IMG_SIZE` to 416

### Issue: Dataset Not Found

**Solution:**
```bash
# Make sure dataset is organized
python organize_dataset.py

# Check if folder exists
ls FabrIQ_Final_Dataset/train/images/
```

## 🎯 Testing Your Model

After training, test on a new image:

```bash
python inference.py \
    --model runs/classify/fabriq_defect_classification/weights/best.pt \
    --source path/to/your/image.jpg \
    --mode classification \
    --save
```

## 💡 Alternative: Use Google Colab (Free GPU!)

If CPU is too slow, use Google Colab for free GPU:

1. Upload your dataset to Google Drive
2. Open Google Colab
3. Mount Drive and run training there
4. Download the trained model

**Colab gives you free GPU for faster training!**

## 📊 Expected Results

After training, you should see:
- **Top-1 Accuracy**: 70-95% (depends on dataset quality)
- **Training Loss**: Decreasing over epochs
- **Validation Accuracy**: Should match training

## ✅ Quick Start Checklist

- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Dataset organized: `python organize_dataset.py`
- [ ] Chose training script: `run_training_cpu.py` (for CPU)
- [ ] Started training
- [ ] Waited for completion (2-6 hours on CPU)
- [ ] Checked results in `runs/classify/` folder
- [ ] Tested model with `inference.py`

## 🎉 You're Ready!

Just run:
```bash
python run_training_cpu.py
```

And wait for training to complete. The script will automatically optimize for CPU and show progress.

**Good luck with your training! 🚀**

