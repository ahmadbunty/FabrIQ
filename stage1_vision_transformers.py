"""
Stage 1: Transformer-Based Visual Understanding
Train/fine-tune ViT and Swin Transformers for image classification
"""

import json
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision.transforms as transforms
from tqdm import tqdm
import timm
from pathlib import Path

class FabricDataset(Dataset):
    """Simple dataset for fabric images"""
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            label = self.labels[idx]
            return image, label, img_path
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
            # Return a black image as fallback
            image = torch.zeros(3, 224, 224)
            return image, self.labels[idx], img_path

class Stage1VisionTransformers:
    """Stage 1: Vision Transformer and Swin Transformer"""
    
    def __init__(self, image_paths, labels, classes, device, output_dir):
        self.image_paths = image_paths
        self.labels = labels
        self.classes = classes
        self.device = device
        self.output_dir = Path(output_dir)
        self.num_classes = len(classes)
        
        # Models
        self.vit_model = None
        self.swin_model = None
        self.vit_embeddings = None
        self.swin_embeddings = None
        
        # Transform
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def create_model(self, model_name, pretrained=True):
        """Create a vision transformer model"""
        if 'vit' in model_name.lower():
            model = timm.create_model(
                'vit_base_patch16_224',
                pretrained=pretrained,
                num_classes=self.num_classes
            )
        elif 'swin' in model_name.lower():
            model = timm.create_model(
                'swin_base_patch4_window7_224',
                pretrained=pretrained,
                num_classes=self.num_classes
            )
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        return model.to(self.device)
    
    def fine_tune_model(self, model, model_name, epochs=3):
        """Fine-tune model on small dataset"""
        print(f"   Fine-tuning {model_name}...")
        
        # Create dataset
        dataset = FabricDataset(self.image_paths, self.labels, self.transform)
        dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
        
        # Setup training
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
        
        model.train()
        for epoch in range(epochs):
            total_loss = 0
            for images, labels, _ in tqdm(dataloader, desc=f"   Epoch {epoch+1}/{epochs}"):
                images = images.to(self.device)
                labels = labels.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            print(f"   Epoch {epoch+1} loss: {total_loss/len(dataloader):.4f}")
        
        model.eval()
        return model
    
    def extract_embeddings(self, model, model_name):
        """Extract feature embeddings from model"""
        print(f"   Extracting {model_name} embeddings...")
        
        dataset = FabricDataset(self.image_paths, self.labels, self.transform)
        dataloader = DataLoader(dataset, batch_size=4, shuffle=False)
        
        embeddings = []
        model.eval()
        
        with torch.no_grad():
            for images, _, _ in dataloader:
                images = images.to(self.device)
                
                # Get features before classification head
                try:
                    # For timm models, use forward_features
                    if hasattr(model, 'forward_features'):
                        features = model.forward_features(images)
                    else:
                        # Fallback: use forward and extract intermediate features
                        # This is a simplified approach - in practice, you'd hook into specific layers
                        output = model(images)
                        # Use the output as a proxy for embeddings (not ideal but works)
                        features = output
                    
                    # Handle different feature shapes
                    if len(features.shape) == 4:  # [B, C, H, W]
                        features = features.mean(dim=[2, 3])  # Global average pooling
                    elif len(features.shape) == 3:  # [B, N, C] for transformers
                        features = features.mean(dim=1)  # Average over sequence
                    elif len(features.shape) == 2:  # [B, C] already flattened
                        pass  # Already in correct shape
                    
                    embeddings.append(features.cpu().numpy())
                except Exception as e:
                    print(f"   Warning: Could not extract features using standard method: {e}")
                    # Fallback: use model output as embedding
                    output = model(images)
                    embeddings.append(output.cpu().numpy())
        
        if embeddings:
            embeddings = np.concatenate(embeddings, axis=0)
        else:
            # Return zero embeddings if extraction failed
            embeddings = np.zeros((len(self.image_paths), 768))
        
        return embeddings
    
    def evaluate_model(self, model, model_name):
        """Evaluate model and return metrics"""
        print(f"   Evaluating {model_name}...")
        
        dataset = FabricDataset(self.image_paths, self.labels, self.transform)
        dataloader = DataLoader(dataset, batch_size=4, shuffle=False)
        
        predictions = []
        confidences = []
        inference_times = []
        correct = 0
        total = 0
        
        model.eval()
        with torch.no_grad():
            for images, labels, _ in dataloader:
                images = images.to(self.device)
                labels = labels.to(self.device)
                
                # Measure inference time
                start_time = time.time()
                outputs = model(images)
                inference_times.append(time.time() - start_time)
                
                probs = torch.softmax(outputs, dim=1)
                conf, preds = torch.max(probs, 1)
                
                predictions.extend(preds.cpu().numpy())
                confidences.extend(conf.cpu().numpy())
                
                correct += (preds == labels).sum().item()
                total += labels.size(0)
        
        accuracy = correct / total if total > 0 else 0
        avg_confidence = np.mean(confidences)
        avg_inference_time = np.mean(inference_times)
        
        results = {
            'model_name': model_name,
            'accuracy': accuracy,
            'avg_confidence': float(avg_confidence),
            'avg_inference_time': float(avg_inference_time),
            'predictions': predictions,
            'confidences': confidences.tolist(),
            'num_samples': len(self.image_paths)
        }
        
        return results
    
    def run(self):
        """Execute Stage 1"""
        print("   Training ViT...")
        self.vit_model = self.create_model('vit', pretrained=True)
        
        # Fine-tune if we have enough data
        if len(self.image_paths) >= 4:
            self.vit_model = self.fine_tune_model(self.vit_model, 'ViT', epochs=2)
        else:
            print("   Skipping fine-tuning (insufficient data)")
        
        vit_results = self.evaluate_model(self.vit_model, 'ViT')
        self.vit_embeddings = self.extract_embeddings(self.vit_model, 'ViT')
        
        print("\n   Training Swin Transformer...")
        self.swin_model = self.create_model('swin', pretrained=True)
        
        if len(self.image_paths) >= 4:
            self.swin_model = self.fine_tune_model(self.swin_model, 'Swin', epochs=2)
        else:
            print("   Skipping fine-tuning (insufficient data)")
        
        swin_results = self.evaluate_model(self.swin_model, 'Swin')
        self.swin_embeddings = self.extract_embeddings(self.swin_model, 'Swin')
        
        # Save results
        with open(self.output_dir / "vit_results.json", 'w') as f:
            json.dump(vit_results, f, indent=2)
        
        with open(self.output_dir / "swin_results.json", 'w') as f:
            json.dump(swin_results, f, indent=2)
        
        print(f"\n   ✅ ViT Accuracy: {vit_results['accuracy']:.4f}")
        print(f"   ✅ Swin Accuracy: {swin_results['accuracy']:.4f}")
        print(f"   ✅ Results saved to {self.output_dir}")
        
        return vit_results, swin_results

