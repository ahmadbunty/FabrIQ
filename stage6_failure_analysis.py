"""
Stage 6: Failure Discovery and Analysis
Identify and save failure cases across all models
"""

import json
import numpy as np
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class Stage6FailureAnalysis:
    """Stage 6: Failure Discovery and Analysis"""
    
    def __init__(self, image_paths, labels, classes,
                 vit_results, swin_results, clip_results,
                 stress_results, output_dir):
        self.image_paths = image_paths
        self.labels = labels
        self.classes = classes
        self.vit_results = vit_results
        self.swin_results = swin_results
        self.clip_results = clip_results
        self.stress_results = stress_results
        self.output_dir = Path(output_dir)
        self.failure_dir = self.output_dir / "failure_cases"
        self.failure_dir.mkdir(exist_ok=True)
    
    def find_vit_swin_disagreements(self):
        """Find images where ViT and Swin disagree"""
        print("   Finding ViT-Swin disagreements...")
        
        disagreements = []
        
        if self.vit_results and self.swin_results:
            vit_preds = self.vit_results.get('predictions', [])
            swin_preds = self.swin_results.get('predictions', [])
            
            for i in range(min(len(vit_preds), len(swin_preds), len(self.image_paths))):
                if vit_preds[i] != swin_preds[i]:
                    disagreements.append({
                        'image_idx': i,
                        'image_path': str(self.image_paths[i]),
                        'true_label': self.classes[self.labels[i]],
                        'vit_prediction': self.classes[vit_preds[i]],
                        'swin_prediction': self.classes[swin_preds[i]],
                        'vit_confidence': self.vit_results.get('confidences', [0])[i] if i < len(self.vit_results.get('confidences', [])) else 0,
                        'swin_confidence': self.swin_results.get('confidences', [0])[i] if i < len(self.swin_results.get('confidences', [])) else 0
                    })
        
        return disagreements
    
    def find_clip_prompt_sensitivity(self):
        """Find cases where CLIP predictions change with prompt wording"""
        print("   Finding CLIP prompt sensitivity cases...")
        
        sensitive_cases = []
        
        if self.clip_results:
            # This is a simplified check - in practice, we'd test multiple prompts
            predictions = self.clip_results.get('zero_shot_predictions', [])
            confidences = self.clip_results.get('zero_shot_confidences', [])
            
            # Find low confidence cases (indicating prompt sensitivity)
            for i in range(min(len(predictions), len(self.image_paths))):
                if confidences[i] < 0.3:  # Low confidence suggests prompt sensitivity
                    sensitive_cases.append({
                        'image_idx': i,
                        'image_path': str(self.image_paths[i]),
                        'true_label': self.classes[self.labels[i]],
                        'clip_prediction': self.classes[predictions[i]] if predictions[i] < len(self.classes) else 'unknown',
                        'confidence': confidences[i]
                    })
        
        return sensitive_cases
    
    def find_generated_image_failures(self):
        """Find generated images that break model assumptions"""
        print("   Finding generated image failures...")
        
        failures = []
        
        if self.stress_results:
            # Check ViT failures on generated images
            if 'vit' in self.stress_results:
                vit_gen = self.stress_results['vit'].get('generated_performance', {})
                gen_confidences = vit_gen.get('confidences', [])
                
                for i, conf in enumerate(gen_confidences):
                    if conf < 0.2:  # Very low confidence
                        failures.append({
                            'type': 'vit_low_confidence',
                            'generated_image_idx': i,
                            'confidence': conf,
                            'description': 'ViT shows very low confidence on generated image'
                        })
            
            # Check Swin failures
            if 'swin' in self.stress_results:
                swin_gen = self.stress_results['swin'].get('generated_performance', {})
                gen_confidences = swin_gen.get('confidences', [])
                
                for i, conf in enumerate(gen_confidences):
                    if conf < 0.2:
                        failures.append({
                            'type': 'swin_low_confidence',
                            'generated_image_idx': i,
                            'confidence': conf,
                            'description': 'Swin shows very low confidence on generated image'
                        })
        
        return failures
    
    def save_failure_visualizations(self, disagreements, clip_sensitive, generated_failures):
        """Save visualizations of failure cases"""
        print("   Saving failure case visualizations...")
        
        # Save ViT-Swin disagreements
        if disagreements:
            self.visualize_disagreements(disagreements[:5])  # Top 5
        
        # Save CLIP sensitive cases
        if clip_sensitive:
            self.visualize_clip_sensitivity(clip_sensitive[:5])
        
        # Save generated failures
        if generated_failures:
            self.visualize_generated_failures(generated_failures[:5])
    
    def visualize_disagreements(self, disagreements):
        """Visualize ViT-Swin disagreements"""
        if not disagreements:
            return
        
        fig, axes = plt.subplots(len(disagreements), 1, figsize=(12, 4*len(disagreements)))
        if len(disagreements) == 1:
            axes = [axes]
        
        for idx, case in enumerate(disagreements):
            try:
                img = Image.open(case['image_path']).convert('RGB')
                axes[idx].imshow(img)
                axes[idx].axis('off')
                title = f"True: {case['true_label']}\nViT: {case['vit_prediction']} ({case['vit_confidence']:.2f})\nSwin: {case['swin_prediction']} ({case['swin_confidence']:.2f})"
                axes[idx].set_title(title, fontsize=10)
            except Exception as e:
                print(f"   Error visualizing {case['image_path']}: {e}")
        
        plt.tight_layout()
        plt.savefig(self.failure_dir / "vit_swin_disagreements.png", dpi=150, bbox_inches='tight')
        plt.close()
    
    def visualize_clip_sensitivity(self, sensitive_cases):
        """Visualize CLIP prompt sensitivity"""
        if not sensitive_cases:
            return
        
        fig, axes = plt.subplots(len(sensitive_cases), 1, figsize=(12, 4*len(sensitive_cases)))
        if len(sensitive_cases) == 1:
            axes = [axes]
        
        for idx, case in enumerate(sensitive_cases):
            try:
                img = Image.open(case['image_path']).convert('RGB')
                axes[idx].imshow(img)
                axes[idx].axis('off')
                title = f"True: {case['true_label']}\nCLIP: {case['clip_prediction']} (conf: {case['confidence']:.2f})"
                axes[idx].set_title(title, fontsize=10)
            except Exception as e:
                print(f"   Error visualizing {case['image_path']}: {e}")
        
        plt.tight_layout()
        plt.savefig(self.failure_dir / "clip_prompt_sensitivity.png", dpi=150, bbox_inches='tight')
        plt.close()
    
    def visualize_generated_failures(self, failures):
        """Visualize generated image failures"""
        # This would require access to generated images
        # For now, we'll create a summary visualization
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        failure_types = {}
        for failure in failures:
            ftype = failure.get('type', 'unknown')
            failure_types[ftype] = failure_types.get(ftype, 0) + 1
        
        if failure_types:
            ax.bar(failure_types.keys(), failure_types.values())
            ax.set_title('Generated Image Failure Types')
            ax.set_ylabel('Count')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(self.failure_dir / "generated_failures_summary.png", dpi=150, bbox_inches='tight')
            plt.close()
    
    def identify_limitations(self):
        """Identify limitations of each architecture"""
        limitations = {
            'vit_limitations': [],
            'swin_limitations': [],
            'clip_limitations': [],
            'gan_limitations': []
        }
        
        # ViT limitations
        if self.vit_results:
            if self.vit_results.get('accuracy', 0) < 0.5:
                limitations['vit_limitations'].append('Low accuracy on small dataset')
            if self.vit_results.get('avg_confidence', 0) < 0.5:
                limitations['vit_limitations'].append('Low prediction confidence')
        
        # Swin limitations
        if self.swin_results:
            if self.swin_results.get('accuracy', 0) < 0.5:
                limitations['swin_limitations'].append('Low accuracy on small dataset')
            if self.swin_results.get('avg_inference_time', 0) > 0.1:
                limitations['swin_limitations'].append('Slower inference time')
        
        # CLIP limitations
        if self.clip_results:
            if self.clip_results.get('zero_shot_accuracy', 0) < 0.4:
                limitations['clip_limitations'].append('Low zero-shot accuracy')
            if len(self.clip_results.get('zero_shot_confidences', [])) > 0:
                avg_conf = np.mean(self.clip_results['zero_shot_confidences'])
                if avg_conf < 0.3:
                    limitations['clip_limitations'].append('High prompt sensitivity')
        
        # GAN limitations
        limitations['gan_limitations'].extend([
            'Mode collapse risk with small datasets',
            'Training instability',
            'Generated images may not match real distribution'
        ])
        
        return limitations
    
    def run(self):
        """Execute Stage 6"""
        print("   Discovering failure cases...")
        
        # Find disagreements
        disagreements = self.find_vit_swin_disagreements()
        
        # Find CLIP sensitivity
        clip_sensitive = self.find_clip_prompt_sensitivity()
        
        # Find generated failures
        generated_failures = self.find_generated_image_failures()
        
        # Save visualizations
        self.save_failure_visualizations(disagreements, clip_sensitive, generated_failures)
        
        # Identify limitations
        limitations = self.identify_limitations()
        
        # Compile results
        results = {
            'cases': {
                'vit_swin_disagreements': disagreements,
                'clip_prompt_sensitivity': clip_sensitive,
                'generated_image_failures': generated_failures
            },
            'vit_limitations': limitations['vit_limitations'],
            'swin_limitations': limitations['swin_limitations'],
            'clip_limitations': limitations['clip_limitations'],
            'gan_limitations': limitations['gan_limitations'],
            'summary': {
                'total_disagreements': len(disagreements),
                'total_clip_sensitive': len(clip_sensitive),
                'total_generated_failures': len(generated_failures)
            }
        }
        
        # Save results
        failure_log_path = self.failure_dir / "failure_cases.json"
        with open(failure_log_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n   ✅ Failure analysis complete")
        print(f"   ✅ Found {len(disagreements)} ViT-Swin disagreements")
        print(f"   ✅ Found {len(clip_sensitive)} CLIP sensitive cases")
        print(f"   ✅ Found {len(generated_failures)} generated image failures")
        print(f"   ✅ Results saved to {failure_log_path}")
        
        return results


