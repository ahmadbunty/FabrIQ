# Visual Reasoning Pipeline

An end-to-end experimental pipeline that combines Vision Transformers, CLIP, GANs, and cross-architectural analysis for intelligent visual reasoning in low-data, ambiguous environments.

## Overview

This pipeline implements a continuous experimental flow where model outputs become inputs, validation, or stress tests for other models. It combines:

- **Supervised Learning**: Vision Transformers (ViT, Swin)
- **Self-Attention**: Transformer architectures
- **Vision-Language Reasoning**: CLIP for zero-shot learning
- **Generative Modeling**: GANs for synthetic data generation

## Pipeline Stages

### Stage 1: Transformer-Based Visual Understanding
- Train/fine-tune ViT for image classification
- Train/fine-tune Swin Transformer
- Evaluate: prediction confidence, accuracy, inference time
- Extract and save feature embeddings and attention representations

### Stage 2: Vision-Language Reasoning with CLIP
- Construct text prompts (correct, ambiguous, competing)
- Zero-shot classification
- Image-text and text-image retrieval
- Compare CLIP outputs with supervised transformers

### Stage 3: Cross-Architectural Embedding Alignment
- Collect embeddings from ViT, Swin, CLIP
- Project to shared low-dimensional space
- Visualize cluster alignment, semantic separation, model disagreements

### Stage 4: Image Generation with GANs
- Train basic GAN (Generator + Discriminator)
- Generate synthetic images
- Evaluate using embedding similarity
- Identify GAN failures (mode collapse, poor diversity, instability)

### Stage 5: Stress Testing with Generated Data
- Pass GAN images through ViT, Swin, CLIP
- Compare prediction confidence (real vs generated)
- Measure embedding drift and failure rates

### Stage 6: Failure Discovery and Analysis
- Identify failure cases:
  - ViT-Swin disagreements
  - CLIP prompt sensitivity
  - Generated images breaking model assumptions
- Save visualizations and logs

## Installation

```bash
pip install -r requirements_visual_reasoning.txt
```

## Usage

### Basic Usage

```bash
python visual_reasoning_pipeline.py
```

### Custom Configuration

```python
from visual_reasoning_pipeline import VisualReasoningPipeline

pipeline = VisualReasoningPipeline(
    dataset_path="FabrIQ_Final_Dataset",
    output_dir="output",
    num_samples=20,  # Use 15-20 images as specified
    device=None  # Auto-detect GPU/CPU
)

pipeline.run()
```

## Output Structure

The pipeline generates the following outputs:

```
output/
├── vit_results.json              # ViT evaluation results
├── swin_results.json             # Swin evaluation results
├── clip_results.json             # CLIP zero-shot and retrieval results
├── embedding_visualization.png   # t-SNE/PCA visualization
├── gan_generated_sample.png      # Sample generated images
├── gan_quality_metrics.json      # GAN quality assessment
├── cross_model_comparison.json   # Stress testing results
├── summary.json                  # Comprehensive summary
└── failure_cases/
    ├── failure_cases.json        # Detailed failure analysis
    ├── vit_swin_disagreements.png
    ├── clip_prompt_sensitivity.png
    └── generated_failures_summary.png
```

## Output Files Explained

### `vit_results.json` / `swin_results.json`
- Model accuracy, average confidence, inference time
- Per-image predictions and confidences

### `clip_results.json`
- Zero-shot classification accuracy
- Image-text and text-image retrieval examples
- Comparison with supervised models

### `embedding_visualization.png`
- 2D projection of embeddings from all models
- Colored by model architecture and semantic class

### `gan_quality_metrics.json`
- Training losses, diversity scores
- Mode collapse detection
- Embedding similarity metrics

### `cross_model_comparison.json`
- Performance on real vs generated images
- Confidence drops, failure rates
- Embedding drift measurements

### `summary.json`
- Consolidated analysis across all stages
- Architecture comparisons
- Identified limitations
- Recommendations

## Dataset Requirements

The pipeline expects images in the following structure:

```
FabrIQ_Final_Dataset/
└── train/
    └── images/
        ├── FabrIQ_class_name_00001.jpg
        ├── FabrIQ_class_name_00002.jpg
        └── ...
```

Images should be named: `FabrIQ_{class_name}_{index}.jpg`

## Class Definitions

The pipeline uses 20 fabric defect classes:
- bad needle line, creases, double kunda, end out, fluff knit
- fly yarn, knit hole, lycra short, mis pattern, mix yarn
- normal, oil lines, oil spot, press off, pulling thread
- run of needle, single kunda, sinker line, tight feeder, yarn variation

## Key Features

1. **Continuous Pipeline**: Each stage feeds into the next
2. **Cross-Model Analysis**: Compare supervised, zero-shot, and generative approaches
3. **Failure Discovery**: Automatic identification of model weaknesses
4. **Embedding Alignment**: Understand semantic relationships across architectures
5. **Stress Testing**: Use generated data to evaluate robustness

## Limitations & Notes

- Designed for small datasets (15-20 images)
- GAN training may be unstable with very small datasets
- CLIP requires internet connection for first-time model download
- Some stages may take time depending on hardware

## Troubleshooting

### CUDA Out of Memory
- Reduce batch size in stage files
- Use CPU mode: `device="cpu"`

### CLIP Model Download Issues
- Ensure internet connection
- CLIP models are downloaded automatically on first use

### Insufficient Data Warnings
- Some stages require minimum 4 images
- Pipeline will skip fine-tuning if insufficient data

## Citation

If you use this pipeline in your research, please cite:

```
Visual Reasoning Pipeline for Multi-Architecture Analysis
Combining Vision Transformers, CLIP, and GANs for Low-Data Environments
```

## License

See main project license.


