"""
Stage 5: Stress Testing Models with Generated Data
Pass GAN images through ViT, Swin, and CLIP to evaluate robustness
"""

import json
import numpy as np
import torch
from PIL import Image
import torchvision.transforms as transforms
from pathlib import Path
import time

class Stage5StressTesting:
    """Stage 5: Stress Testing with Generated Data"""
    
    def __init__(self, generated_images, real_image_paths, labels, classes,
                 vit_model, swin_model, clip_model, device, output_dir):
        self.generated_images = generated_images
        self.real_image_paths = real_image_paths
        self.labels = labels
        self.classes = classes
        self.vit_model = vit_model
        self.swin_model = swin_model
        self.clip_model = clip_model
        self.device = device
        self.output_dir = Path(output_dir)
        
        # Transforms
        self.vit_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        self.clip_transform = None  # Will use CLIP's preprocess
    
    def test_model_on_generated(self, model, model_name, transform):
        """Test a model on generated images"""
        print(f"   Testing {model_name} on generated images...")
        
        predictions = []
        confidences = []
        inference_times = []
        
        model.eval()
        with torch.no_grad():
            for img_tensor in self.generated_images:
                # Convert tensor to PIL Image
                img_np = img_tensor.permute(1, 2, 0).numpy()
                img_np = np.clip(img_np, 0, 1)
                img_pil = Image.fromarray((img_np * 255).astype(np.uint8))
                
                # Transform
                if transform:
                    img_tensor = transform(img_pil).unsqueeze(0).to(self.device)
                else:
                    img_tensor = img_tensor.unsqueeze(0).to(self.device)
                
                # Inference
                start_time = time.time()
                output = model(img_tensor)
                inference_times.append(time.time() - start_time)
                
                # Get prediction
                if hasattr(output, 'logits'):
                    output = output.logits
                probs = torch.softmax(output, dim=1)
                conf, pred = torch.max(probs, 1)
                
                predictions.append(pred.item())
                confidences.append(conf.item())
        
        return {
            'predictions': predictions,
            'confidences': confidences,
            'avg_confidence': float(np.mean(confidences)),
            'avg_inference_time': float(np.mean(inference_times))
        }
    
    def test_model_on_real(self, model, model_name, transform, image_paths):
        """Test a model on real images"""
        predictions = []
        confidences = []
        
        model.eval()
        with torch.no_grad():
            for img_path in image_paths:
                try:
                    image = Image.open(img_path).convert('RGB')
                    if transform:
                        img_tensor = transform(image).unsqueeze(0).to(self.device)
                    else:
                        img_tensor = self.vit_transform(image).unsqueeze(0).to(self.device)
                    
                    output = model(img_tensor)
                    if hasattr(output, 'logits'):
                        output = output.logits
                    probs = torch.softmax(output, dim=1)
                    conf, pred = torch.max(probs, 1)
                    
                    predictions.append(pred.item())
                    confidences.append(conf.item())
                except Exception as e:
                    print(f"   Error processing {img_path}: {e}")
                    predictions.append(0)
                    confidences.append(0.0)
        
        return {
            'predictions': predictions,
            'confidences': confidences,
            'avg_confidence': float(np.mean(confidences))
        }
    
    def compute_embedding_drift(self, real_embeddings, generated_embeddings):
        """Compute embedding drift between real and generated"""
        if real_embeddings is None or generated_embeddings is None:
            return None
        
        # Compute mean embeddings
        real_mean = np.mean(real_embeddings, axis=0)
        gen_mean = np.mean(generated_embeddings, axis=0)
        
        # Compute drift
        drift = np.linalg.norm(real_mean - gen_mean)
        
        # Compute distribution shift
        real_std = np.std(real_embeddings, axis=0)
        gen_std = np.std(generated_embeddings, axis=0)
        std_shift = np.linalg.norm(real_std - gen_std)
        
        return {
            'mean_drift': float(drift),
            'std_shift': float(std_shift)
        }
    
    def compute_failure_rate(self, real_results, generated_results):
        """Compute failure rate on generated vs real"""
        # Failure = very low confidence
        real_failures = sum(1 for c in real_results['confidences'] if c < 0.3)
        gen_failures = sum(1 for c in generated_results['confidences'] if c < 0.3)
        
        real_failure_rate = real_failures / len(real_results['confidences']) if len(real_results['confidences']) > 0 else 0
        gen_failure_rate = gen_failures / len(generated_results['confidences']) if len(generated_results['confidences']) > 0 else 0
        
        return {
            'real_failure_rate': float(real_failure_rate),
            'generated_failure_rate': float(gen_failure_rate),
            'failure_rate_increase': float(gen_failure_rate - real_failure_rate)
        }
    
    def run(self):
        """Execute Stage 5"""
        print("   Stress testing models with generated images...")
        
        results = {}
        
        # Test ViT
        if self.vit_model is not None:
            print("   Testing ViT...")
            vit_real = self.test_model_on_real(
                self.vit_model, 'ViT', self.vit_transform, self.real_image_paths[:len(self.generated_images)]
            )
            vit_generated = self.test_model_on_generated(
                self.vit_model, 'ViT', self.vit_transform
            )
            
            vit_failures = self.compute_failure_rate(vit_real, vit_generated)
            
            results['vit'] = {
                'real_performance': vit_real,
                'generated_performance': vit_generated,
                'confidence_drop': float(vit_real['avg_confidence'] - vit_generated['avg_confidence']),
                'failure_rates': vit_failures
            }
        
        # Test Swin
        if self.swin_model is not None:
            print("   Testing Swin...")
            swin_real = self.test_model_on_real(
                self.swin_model, 'Swin', self.vit_transform, self.real_image_paths[:len(self.generated_images)]
            )
            swin_generated = self.test_model_on_generated(
                self.swin_model, 'Swin', self.vit_transform
            )
            
            swin_failures = self.compute_failure_rate(swin_real, swin_generated)
            
            results['swin'] = {
                'real_performance': swin_real,
                'generated_performance': swin_generated,
                'confidence_drop': float(swin_real['avg_confidence'] - swin_generated['avg_confidence']),
                'failure_rates': swin_failures
            }
        
        # Test CLIP (if available)
        if self.clip_model is not None:
            print("   Testing CLIP...")
            # CLIP requires different handling
            clip_generated = self.test_clip_on_generated()
            results['clip'] = {
                'generated_performance': clip_generated
            }
        
        # Save results
        with open(self.output_dir / "cross_model_comparison.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n   ✅ Stress testing complete")
        print(f"   ✅ Results saved to {self.output_dir / 'cross_model_comparison.json'}")
        
        return results
    
    def test_clip_on_generated(self):
        """Test CLIP on generated images"""
        import clip
        
        if not hasattr(self.clip_model, 'encode_image'):
            return {'confidences': [], 'avg_confidence': 0.0}
        
        confidences = []
        self.clip_model.eval()
        
        # Create text prompts
        text_descriptions = [f"a photo of {cls}" for cls in self.classes]
        text_tokens = clip.tokenize(text_descriptions).to(self.device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            for img_tensor in self.generated_images:
                # Convert to PIL
                img_np = img_tensor.permute(1, 2, 0).numpy()
                img_np = np.clip(img_np, 0, 1)
                img_pil = Image.fromarray((img_np * 255).astype(np.uint8))
                
                # Use CLIP preprocess (simplified version)
                try:
                    # Resize and normalize for CLIP
                    img_pil = img_pil.resize((224, 224))
                    img_tensor_clip = transforms.ToTensor()(img_pil).unsqueeze(0).to(self.device)
                    img_tensor_clip = transforms.Normalize(
                        mean=[0.48145466, 0.4578275, 0.40821073],
                        std=[0.26862954, 0.26130258, 0.27577711]
                    )(img_tensor_clip)
                    
                    image_features = self.clip_model.encode_image(img_tensor_clip)
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    
                    similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                    conf = similarity.max().item()
                    confidences.append(conf)
                except Exception as e:
                    print(f"   Error in CLIP test: {e}")
                    confidences.append(0.0)
        
        return {
            'confidences': confidences,
            'avg_confidence': float(np.mean(confidences)) if confidences else 0.0
        }

