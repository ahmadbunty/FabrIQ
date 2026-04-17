#!/usr/bin/env python
"""
Quick start script for Visual Reasoning Pipeline
"""

import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Visual Reasoning Pipeline')
    parser.add_argument('--dataset', type=str, default='FabrIQ_Final_Dataset',
                       help='Path to dataset directory')
    parser.add_argument('--output', type=str, default='output',
                       help='Output directory')
    parser.add_argument('--num-samples', type=int, default=20,
                       help='Number of images to use (default: 20)')
    parser.add_argument('--device', type=str, default=None,
                       help='Device to use (cuda/cpu), auto-detect if not specified')
    
    args = parser.parse_args()
    
    # Check if dataset exists
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"❌ Error: Dataset not found at {dataset_path}")
        print(f"   Please ensure the dataset directory exists")
        sys.exit(1)
    
    # Check if train/images exists
    train_images = dataset_path / "train" / "images"
    if not train_images.exists():
        print(f"❌ Error: Train images not found at {train_images}")
        print(f"   Expected structure: {dataset_path}/train/images/")
        sys.exit(1)
    
    # Import and run pipeline
    try:
        from visual_reasoning_pipeline import VisualReasoningPipeline
        
        print("="*80)
        print("🔬 VISUAL REASONING PIPELINE")
        print("="*80)
        print(f"Dataset: {args.dataset}")
        print(f"Output: {args.output}")
        print(f"Samples: {args.num_samples}")
        print(f"Device: {args.device or 'auto-detect'}")
        print("="*80)
        
        pipeline = VisualReasoningPipeline(
            dataset_path=args.dataset,
            output_dir=args.output,
            num_samples=args.num_samples,
            device=args.device
        )
        
        pipeline.run()
        
    except ImportError as e:
        print(f"❌ Error: Could not import pipeline modules: {e}")
        print("   Make sure all required packages are installed:")
        print("   pip install -r requirements_visual_reasoning.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()


