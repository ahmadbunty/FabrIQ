"""
End-to-End Visual Reasoning Pipeline
Combines Vision Transformers, CLIP, GANs, and Cross-Architectural Analysis
"""

import os
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision.transforms as transforms
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Stage imports - handle import errors gracefully
try:
    from stage1_vision_transformers import Stage1VisionTransformers
    from stage2_clip_reasoning import Stage2CLIPReasoning
    from stage3_embedding_alignment import Stage3EmbeddingAlignment
    from stage4_gan_generation import Stage4GANGeneration
    from stage5_stress_testing import Stage5StressTesting
    from stage6_failure_analysis import Stage6FailureAnalysis
except ImportError as e:
    print(f"Warning: Could not import stage modules: {e}")
    print("Make sure all stage files are in the same directory")

class VisualReasoningPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, 
                 dataset_path: str = "FabrIQ_Final_Dataset",
                 output_dir: str = "output",
                 num_samples: int = 20,
                 device: str = None):
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.num_samples = num_samples
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "failure_cases").mkdir(exist_ok=True)
        
        # Class definitions
        self.classes = [
            'bad needle line', 'creases', 'double kunda', 'end out', 'fluff knit',
            'fly yarn', 'knit hole', 'lycra short', 'mis pattern', 'mix yarn',
            'normal', 'oil lines', 'oil spot', 'press off', 'pulling thread',
            'run of needle', 'single kunda', 'sinker line', 'tight feeder', 'yarn variation'
        ]
        
        # Pipeline state
        self.state = {
            'vit_results': None,
            'swin_results': None,
            'clip_results': None,
            'embeddings': {},
            'gan_model': None,
            'generated_images': None,
            'failure_cases': []
        }
        
        print(f"🚀 Visual Reasoning Pipeline Initialized")
        print(f"   Dataset: {self.dataset_path}")
        print(f"   Output: {self.output_dir}")
        print(f"   Device: {self.device}")
        print(f"   Classes: {len(self.classes)}")
    
    def load_dataset(self) -> Tuple[List[str], List[int]]:
        """Load a small subset of images for experimentation"""
        image_paths = []
        labels = []
        
        # Collect images from train split
        train_dir = self.dataset_path / "train" / "images"
        if not train_dir.exists():
            raise FileNotFoundError(f"Dataset not found: {train_dir}")
        
        # Get all images
        all_images = list(train_dir.glob("*.jpg"))[:self.num_samples]
        
        for img_path in all_images:
            # Extract class from filename: FabrIQ_class_name_00001.jpg
            parts = img_path.stem.split('_')
            if len(parts) >= 2 and parts[0] == 'FabrIQ':
                class_parts = parts[1:-1]
                class_name = ' '.join(class_parts)
                
                if class_name in self.classes:
                    image_paths.append(str(img_path))
                    labels.append(self.classes.index(class_name))
        
        print(f"📊 Loaded {len(image_paths)} images from dataset")
        return image_paths, labels
    
    def run(self):
        """Execute all pipeline stages"""
        print("\n" + "="*80)
        print("🔬 VISUAL REASONING PIPELINE - EXECUTION")
        print("="*80)
        
        # Load dataset
        image_paths, labels = self.load_dataset()
        
        # Stage 1: Vision Transformers
        print("\n" + "="*80)
        print("STAGE 1: Vision Transformer-Based Visual Understanding")
        print("="*80)
        stage1 = Stage1VisionTransformers(
            image_paths, labels, self.classes, self.device, self.output_dir
        )
        vit_results, swin_results = stage1.run()
        self.state['vit_results'] = vit_results
        self.state['swin_results'] = swin_results
        self.state['embeddings']['vit'] = stage1.vit_embeddings
        self.state['embeddings']['swin'] = stage1.swin_embeddings
        
        # Stage 2: CLIP Vision-Language Reasoning
        print("\n" + "="*80)
        print("STAGE 2: Vision-Language Reasoning with CLIP")
        print("="*80)
        stage2 = Stage2CLIPReasoning(
            image_paths, labels, self.classes, self.device, self.output_dir
        )
        clip_results = stage2.run()
        self.state['clip_results'] = clip_results
        self.state['embeddings']['clip'] = stage2.clip_embeddings
        
        # Compare with supervised models
        comparison = stage2.compare_with_supervised(vit_results, swin_results)
        clip_results.update(comparison)
        
        # Stage 3: Cross-Architectural Embedding Alignment
        print("\n" + "="*80)
        print("STAGE 3: Cross-Architectural Embedding Alignment")
        print("="*80)
        stage3 = Stage3EmbeddingAlignment(
            self.state['embeddings'], image_paths, labels, 
            self.classes, self.output_dir
        )
        alignment_results = stage3.run()
        
        # Stage 4: GAN Generation
        print("\n" + "="*80)
        print("STAGE 4: Image Generation with GANs")
        print("="*80)
        stage4 = Stage4GANGeneration(
            image_paths, labels, self.classes, self.device, self.output_dir
        )
        gan_results, gan_model, generated_images = stage4.run()
        self.state['gan_model'] = gan_model
        self.state['generated_images'] = generated_images
        
        # Stage 5: Stress Testing with Generated Data
        print("\n" + "="*80)
        print("STAGE 5: Stress Testing Models with Generated Data")
        print("="*80)
        stage5 = Stage5StressTesting(
            generated_images, image_paths, labels, self.classes,
            stage1.vit_model, stage1.swin_model, stage2.clip_model,
            self.device, self.output_dir
        )
        stress_results = stage5.run()
        
        # Update clip_results with comparison data
        if 'clip_success_count' not in clip_results:
            comparison = stage2.compare_with_supervised(vit_results, swin_results)
            clip_results.update(comparison)
        
        # Stage 6: Failure Discovery and Analysis
        print("\n" + "="*80)
        print("STAGE 6: Failure Discovery and Analysis")
        print("="*80)
        stage6 = Stage6FailureAnalysis(
            image_paths, labels, self.classes,
            vit_results, swin_results, clip_results,
            stress_results, self.output_dir
        )
        failure_results = stage6.run()
        self.state['failure_cases'] = failure_results
        
        # Generate final summary
        self.generate_summary(
            vit_results, swin_results, clip_results,
            alignment_results, gan_results, stress_results, failure_results
        )
        
        print("\n" + "="*80)
        print("✅ PIPELINE COMPLETE")
        print("="*80)
        print(f"📁 All results saved to: {self.output_dir}")
    
    def generate_summary(self, vit_results, swin_results, clip_results,
                        alignment_results, gan_results, stress_results, failure_results):
        """Generate comprehensive summary JSON"""
        summary = {
            "pipeline_metadata": {
                "num_images": self.num_samples,
                "num_classes": len(self.classes),
                "device": self.device
            },
            "stage1_vision_transformers": {
                "vit_vs_swin": {
                    "vit_accuracy": vit_results.get('accuracy', 0),
                    "swin_accuracy": swin_results.get('accuracy', 0),
                    "vit_avg_confidence": vit_results.get('avg_confidence', 0),
                    "swin_avg_confidence": swin_results.get('avg_confidence', 0),
                    "vit_inference_time": vit_results.get('avg_inference_time', 0),
                    "swin_inference_time": swin_results.get('avg_inference_time', 0)
                },
                "conclusion": "ViT and Swin show different strengths in visual understanding"
            },
            "stage2_clip_reasoning": {
                "supervised_vs_zero_shot": {
                    "supervised_accuracy": (vit_results.get('accuracy', 0) + swin_results.get('accuracy', 0)) / 2,
                    "clip_zero_shot_accuracy": clip_results.get('zero_shot_accuracy', 0),
                    "clip_success_where_supervised_failed": clip_results.get('clip_success_count', 0),
                    "supervised_success_where_clip_failed": clip_results.get('supervised_success_count', 0)
                },
                "conclusion": "CLIP provides complementary reasoning through language supervision"
            },
            "stage3_embedding_alignment": {
                "cross_model_behavior": alignment_results,
                "conclusion": "Embeddings show semantic alignment with some architectural differences"
            },
            "stage4_gan_generation": {
                "gan_quality_metrics": gan_results,
                "conclusion": "GAN demonstrates generation capabilities with identified limitations"
            },
            "stage5_stress_testing": {
                "gan_impact_on_recognition": stress_results,
                "conclusion": "Generated images reveal model robustness and generalization gaps"
            },
            "stage6_failure_analysis": {
                "identified_limitations": {
                    "vit_limitations": failure_results.get('vit_limitations', []),
                    "swin_limitations": failure_results.get('swin_limitations', []),
                    "clip_limitations": failure_results.get('clip_limitations', []),
                    "gan_limitations": failure_results.get('gan_limitations', [])
                },
                "failure_cases_count": len(failure_results.get('cases', [])),
                "conclusion": "Failure cases highlight architectural weaknesses and improvement opportunities"
            },
            "overall_conclusions": {
                "architecture_comparison": "Each architecture (ViT, Swin, CLIP) has unique strengths and weaknesses",
                "generative_modeling": "GANs enable stress testing but reveal training instabilities",
                "cross_architectural_insights": "Embedding alignment reveals semantic understanding differences",
                "recommendations": [
                    "Combine supervised and zero-shot approaches for robustness",
                    "Use embedding alignment for model ensemble",
                    "Address GAN mode collapse for better synthetic data",
                    "Leverage failure cases for targeted dataset augmentation"
                ]
            }
        }
        
        summary_path = self.output_dir / "summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Summary saved to: {summary_path}")

if __name__ == "__main__":
    pipeline = VisualReasoningPipeline(
        dataset_path="FabrIQ_Final_Dataset",
        output_dir="output",
        num_samples=20,  # Use 15-20 images as specified
        device=None  # Auto-detect
    )
    pipeline.run()

