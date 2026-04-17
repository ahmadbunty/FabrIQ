"""
Stage 2: Vision-Language Reasoning with CLIP
Zero-shot classification, image-text retrieval, and comparison with supervised models
"""

import json
import numpy as np
import torch
from PIL import Image
import clip
from pathlib import Path
from tqdm import tqdm

class Stage2CLIPReasoning:
    """Stage 2: CLIP Vision-Language Reasoning"""
    
    def __init__(self, image_paths, labels, classes, device, output_dir):
        self.image_paths = image_paths
        self.labels = labels
        self.classes = classes
        self.device = device
        self.output_dir = Path(output_dir)
        
        # CLIP model
        self.clip_model = None
        self.clip_preprocess = None
        self.clip_embeddings = None
    
    def load_clip_model(self):
        """Load CLIP model"""
        print("   Loading CLIP model...")
        model, preprocess = clip.load("ViT-B/32", device=self.device)
        self.clip_model = model
        self.clip_preprocess = preprocess
        print("   ✅ CLIP model loaded")
    
    def create_prompts(self):
        """Create text prompts: correct, ambiguous, and competing"""
        prompts = {
            'correct': [],
            'ambiguous': [],
            'competing': []
        }
        
        for cls in self.classes:
            # Correct prompts
            prompts['correct'].append(f"a photo of {cls}")
            prompts['correct'].append(f"an image showing {cls}")
            prompts['correct'].append(f"fabric defect: {cls}")
            
            # Ambiguous prompts
            prompts['ambiguous'].append(f"something like {cls}")
            prompts['ambiguous'].append(f"possibly {cls}")
            prompts['ambiguous'].append(f"maybe {cls} or similar")
            
            # Competing prompts (similar classes)
            if cls != 'normal':
                prompts['competing'].append(f"defective fabric")
                prompts['competing'].append(f"fabric with issues")
        
        # Add some generic prompts
        prompts['competing'].extend([
            "a normal fabric",
            "perfect fabric",
            "flawless material"
        ])
        
        return prompts
    
    def extract_image_embeddings(self):
        """Extract CLIP image embeddings"""
        print("   Extracting CLIP image embeddings...")
        
        embeddings = []
        self.clip_model.eval()
        
        with torch.no_grad():
            for img_path in tqdm(self.image_paths, desc="   Processing images"):
                try:
                    image = Image.open(img_path).convert('RGB')
                    image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
                    image_features = self.clip_model.encode_image(image_tensor)
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    embeddings.append(image_features.cpu().numpy())
                except Exception as e:
                    print(f"   Error processing {img_path}: {e}")
                    embeddings.append(np.zeros((1, 512)))  # Fallback
        
        self.clip_embeddings = np.concatenate(embeddings, axis=0)
        return self.clip_embeddings
    
    def zero_shot_classification(self):
        """Perform zero-shot classification"""
        print("   Performing zero-shot classification...")
        
        # Create text prompts for all classes
        text_descriptions = [f"a photo of {cls}" for cls in self.classes]
        text_tokens = clip.tokenize(text_descriptions).to(self.device)
        
        # Get text embeddings
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # Classify images
        predictions = []
        confidences = []
        correct = 0
        
        with torch.no_grad():
            for i, img_path in enumerate(self.image_paths):
                try:
                    image = Image.open(img_path).convert('RGB')
                    image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
                    image_features = self.clip_model.encode_image(image_tensor)
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                    
                    # Compute similarity
                    similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
                    conf, pred = similarity.max(dim=-1)
                    
                    predictions.append(pred.item())
                    confidences.append(conf.item())
                    
                    if pred.item() == self.labels[i]:
                        correct += 1
                except Exception as e:
                    print(f"   Error classifying {img_path}: {e}")
                    predictions.append(0)
                    confidences.append(0.0)
        
        accuracy = correct / len(self.image_paths) if len(self.image_paths) > 0 else 0
        
        return {
            'predictions': predictions,
            'confidences': confidences,
            'accuracy': accuracy
        }
    
    def image_text_retrieval(self, query_text):
        """Retrieve images matching text query"""
        print(f"   Image-text retrieval for: '{query_text}'")
        
        text_tokens = clip.tokenize([query_text]).to(self.device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        similarities = []
        for i, img_path in enumerate(self.image_paths):
            try:
                image = Image.open(img_path).convert('RGB')
                image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
                image_features = self.clip_model.encode_image(image_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                similarity = (image_features @ text_features.T).item()
                similarities.append((i, similarity, img_path))
            except Exception as e:
                print(f"   Error processing {img_path}: {e}")
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def text_image_retrieval(self, query_image_idx):
        """Retrieve text descriptions matching image"""
        print(f"   Text-image retrieval for image {query_image_idx}")
        
        # Get image embedding
        img_path = self.image_paths[query_image_idx]
        image = Image.open(img_path).convert('RGB')
        image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            image_features = self.clip_model.encode_image(image_tensor)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        # Create text prompts
        prompts = self.create_prompts()
        all_prompts = prompts['correct'] + prompts['ambiguous'][:5] + prompts['competing'][:5]
        text_tokens = clip.tokenize(all_prompts).to(self.device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            similarities = (image_features @ text_features.T).squeeze()
            top_indices = similarities.argsort(descending=True)[:5]
        
        results = [(all_prompts[idx], similarities[idx].item()) for idx in top_indices]
        return results
    
    def compare_with_supervised(self, vit_results, swin_results):
        """Compare CLIP predictions with supervised models"""
        print("   Comparing CLIP with supervised models...")
        
        zero_shot_results = self.zero_shot_classification()
        clip_preds = zero_shot_results['predictions']
        vit_preds = vit_results.get('predictions', [])
        swin_preds = swin_results.get('predictions', [])
        
        clip_success_supervised_failed = 0
        supervised_success_clip_failed = 0
        
        min_len = min(len(clip_preds), len(vit_preds), len(swin_preds), len(self.image_paths))
        
        for i in range(min_len):
            correct_label = self.labels[i]
            clip_correct = clip_preds[i] == correct_label
            vit_correct = vit_preds[i] == correct_label if i < len(vit_preds) else False
            swin_correct = swin_preds[i] == correct_label if i < len(swin_preds) else False
            supervised_correct = vit_correct or swin_correct
            
            if clip_correct and not supervised_correct:
                clip_success_supervised_failed += 1
            if supervised_correct and not clip_correct:
                supervised_success_clip_failed += 1
        
        return {
            'clip_success_count': clip_success_supervised_failed,
            'supervised_success_count': supervised_success_clip_failed
        }
    
    def run(self):
        """Execute Stage 2"""
        # Load CLIP
        self.load_clip_model()
        
        # Extract embeddings
        self.extract_image_embeddings()
        
        # Zero-shot classification
        zero_shot_results = self.zero_shot_classification()
        
        # Image-text retrieval examples
        retrieval_examples = []
        for query in ["fabric defect", "normal fabric", "knit hole"]:
            results = self.image_text_retrieval(query)
            retrieval_examples.append({
                'query': query,
                'top_matches': [(str(r[2]), r[1]) for r in results[:3]]
            })
        
        # Text-image retrieval examples
        text_retrieval_examples = []
        for i in range(min(3, len(self.image_paths))):
            results = self.text_image_retrieval(i)
            text_retrieval_examples.append({
                'image_idx': i,
                'top_text_matches': results
            })
        
        # Compile results
        results = {
            'zero_shot_accuracy': zero_shot_results['accuracy'],
            'zero_shot_predictions': zero_shot_results['predictions'],
            'zero_shot_confidences': zero_shot_results['confidences'],
            'image_text_retrieval': retrieval_examples,
            'text_image_retrieval': text_retrieval_examples,
            'num_samples': len(self.image_paths)
        }
        
        # Save results
        with open(self.output_dir / "clip_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n   ✅ CLIP Zero-shot Accuracy: {zero_shot_results['accuracy']:.4f}")
        print(f"   ✅ Results saved to {self.output_dir / 'clip_results.json'}")
        
        return results

