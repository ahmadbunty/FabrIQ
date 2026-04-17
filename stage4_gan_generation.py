"""
Stage 4: Image Generation with GANs
Train GAN and generate synthetic images for stress testing
"""

import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision.transforms as transforms
from pathlib import Path
import matplotlib.pyplot as plt
from tqdm import tqdm

class FabricDataset(Dataset):
    """Dataset for GAN training"""
    def __init__(self, image_paths, transform=None):
        self.image_paths = image_paths
        self.transform = transform or transforms.Compose([
            transforms.Resize((64, 64)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            if self.transform:
                image = self.transform(image)
            return image
        except Exception as e:
            print(f"Error loading {img_path}: {e}")
            return torch.zeros(3, 64, 64)

class Generator(nn.Module):
    """Simple GAN Generator"""
    def __init__(self, nz=100, ngf=64, nc=3):
        super(Generator, self).__init__()
        self.main = nn.Sequential(
            nn.ConvTranspose2d(nz, ngf * 8, 4, 1, 0, bias=False),
            nn.BatchNorm2d(ngf * 8),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 8, ngf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 4),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 4, ngf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 2),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 2, nc, 4, 2, 1, bias=False),
            nn.Tanh()
        )
    
    def forward(self, input):
        return self.main(input)

class Discriminator(nn.Module):
    """Simple GAN Discriminator"""
    def __init__(self, nc=3, ndf=64):
        super(Discriminator, self).__init__()
        self.main = nn.Sequential(
            nn.Conv2d(nc, ndf, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf, ndf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 2, ndf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 4, 1, 4, 1, 0, bias=False),
            nn.Sigmoid()
        )
    
    def forward(self, input):
        return self.main(input).view(-1, 1).squeeze(1)

class Stage4GANGeneration:
    """Stage 4: GAN Generation"""
    
    def __init__(self, image_paths, labels, classes, device, output_dir):
        self.image_paths = image_paths
        self.labels = labels
        self.classes = classes
        self.device = device
        self.output_dir = Path(output_dir)
        
        self.generator = None
        self.discriminator = None
        self.generated_images = None
    
    def train_gan(self, epochs=10, batch_size=4, nz=100):
        """Train GAN"""
        print("   Training GAN...")
        
        # Create dataset
        dataset = FabricDataset(self.image_paths)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Initialize models
        self.generator = Generator(nz=nz).to(self.device)
        self.discriminator = Discriminator().to(self.device)
        
        # Loss and optimizers
        criterion = nn.BCELoss()
        lr = 0.0002
        beta1 = 0.5
        optimizerG = optim.Adam(self.generator.parameters(), lr=lr, betas=(beta1, 0.999))
        optimizerD = optim.Adam(self.discriminator.parameters(), lr=lr, betas=(beta1, 0.999))
        
        # Training labels
        real_label = 1.0
        fake_label = 0.0
        
        # Training loop
        g_losses = []
        d_losses = []
        
        for epoch in range(epochs):
            epoch_g_loss = 0
            epoch_d_loss = 0
            
            for i, real_images in enumerate(tqdm(dataloader, desc=f"   Epoch {epoch+1}/{epochs}")):
                batch_size = real_images.size(0)
                real_images = real_images.to(self.device)
                
                # Train Discriminator
                self.discriminator.zero_grad()
                
                # Real images
                label = torch.full((batch_size,), real_label, dtype=torch.float, device=self.device)
                output = self.discriminator(real_images)
                errD_real = criterion(output, label)
                errD_real.backward()
                
                # Fake images
                noise = torch.randn(batch_size, 100, 1, 1, device=self.device)
                fake = self.generator(noise)
                label.fill_(fake_label)
                output = self.discriminator(fake.detach())
                errD_fake = criterion(output, label)
                errD_fake.backward()
                
                errD = errD_real + errD_fake
                optimizerD.step()
                
                # Train Generator
                self.generator.zero_grad()
                label.fill_(real_label)
                output = self.discriminator(fake)
                errG = criterion(output, label)
                errG.backward()
                optimizerG.step()
                
                epoch_g_loss += errG.item()
                epoch_d_loss += errD.item()
            
            avg_g_loss = epoch_g_loss / len(dataloader)
            avg_d_loss = epoch_d_loss / len(dataloader)
            g_losses.append(avg_g_loss)
            d_losses.append(avg_d_loss)
            
            print(f"   Epoch {epoch+1}: G_loss={avg_g_loss:.4f}, D_loss={avg_d_loss:.4f}")
        
        print("   ✅ GAN training complete")
        return g_losses, d_losses
    
    def generate_images(self, num_images=10, nz=100):
        """Generate synthetic images"""
        print(f"   Generating {num_images} synthetic images...")
        
        if self.generator is None:
            print("   ⚠️ Generator not trained, using random initialization")
            self.generator = Generator(nz=nz).to(self.device)
        
        self.generator.eval()
        generated_images = []
        
        with torch.no_grad():
            for _ in range(num_images):
                noise = torch.randn(1, nz, 1, 1, device=self.device)
                fake_image = self.generator(noise)
                # Denormalize
                fake_image = (fake_image + 1) / 2.0
                fake_image = torch.clamp(fake_image, 0, 1)
                generated_images.append(fake_image.cpu())
        
        self.generated_images = generated_images
        
        # Save sample
        self.save_generated_samples(generated_images[:8])
        
        return generated_images
    
    def save_generated_samples(self, images):
        """Save generated image samples"""
        fig, axes = plt.subplots(2, 4, figsize=(12, 6))
        axes = axes.flatten()
        
        for i, img_tensor in enumerate(images[:8]):
            img = img_tensor.permute(1, 2, 0).numpy()
            img = np.clip(img, 0, 1)
            axes[i].imshow(img)
            axes[i].axis('off')
            axes[i].set_title(f'Generated {i+1}')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "gan_generated_sample.png", dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"   ✅ Generated samples saved to {self.output_dir / 'gan_generated_sample.png'}")
    
    def evaluate_gan_quality(self, real_embeddings=None):
        """Evaluate GAN quality metrics"""
        print("   Evaluating GAN quality...")
        
        metrics = {
            'num_generated': len(self.generated_images) if self.generated_images else 0,
            'mode_collapse_detected': False,
            'diversity_score': 0.0,
            'training_stability': 'unknown'
        }
        
        if self.generated_images:
            # Check for mode collapse (low diversity)
            generated_tensors = torch.stack(self.generated_images)
            # Compute variance across generated images
            variance = torch.var(generated_tensors.view(len(self.generated_images), -1), dim=0).mean().item()
            metrics['diversity_score'] = float(variance)
            
            # Mode collapse if variance is very low
            if variance < 0.01:
                metrics['mode_collapse_detected'] = True
        
        # Embedding similarity (if real embeddings provided)
        if real_embeddings is not None and self.generated_images:
            # This would require extracting embeddings from generated images
            # For now, we'll use a placeholder
            metrics['embedding_similarity'] = 0.5  # Placeholder
        
        return metrics
    
    def identify_gan_failures(self):
        """Identify GAN failure modes"""
        failures = []
        
        if self.generated_images is None:
            failures.append("No images generated")
            return failures
        
        # Check for mode collapse
        generated_tensors = torch.stack(self.generated_images)
        variance = torch.var(generated_tensors.view(len(self.generated_images), -1), dim=0).mean().item()
        
        if variance < 0.01:
            failures.append({
                'type': 'mode_collapse',
                'description': 'Generated images lack diversity',
                'variance': variance
            })
        
        # Check for poor quality (very dark or very bright)
        mean_brightness = generated_tensors.mean().item()
        if mean_brightness < 0.1 or mean_brightness > 0.9:
            failures.append({
                'type': 'poor_quality',
                'description': 'Generated images have extreme brightness',
                'mean_brightness': mean_brightness
            })
        
        return failures
    
    def run(self):
        """Execute Stage 4"""
        # Train GAN
        if len(self.image_paths) >= 4:
            g_losses, d_losses = self.train_gan(epochs=5, batch_size=min(4, len(self.image_paths)))
        else:
            print("   ⚠️ Insufficient data for GAN training, using pre-initialized generator")
            self.generator = Generator().to(self.device)
            g_losses, d_losses = [], []
        
        # Generate images
        num_generate = min(10, len(self.image_paths))
        generated_images = self.generate_images(num_images=num_generate)
        
        # Evaluate quality
        quality_metrics = self.evaluate_gan_quality()
        
        # Identify failures
        failures = self.identify_gan_failures()
        
        # Compile results
        results = {
            'training_losses': {
                'generator_losses': g_losses,
                'discriminator_losses': d_losses
            },
            'quality_metrics': quality_metrics,
            'failures': failures,
            'num_generated': len(generated_images)
        }
        
        # Save results
        with open(self.output_dir / "gan_quality_metrics.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n   ✅ GAN generation complete")
        print(f"   ✅ Generated {len(generated_images)} images")
        print(f"   ✅ Results saved to {self.output_dir / 'gan_quality_metrics.json'}")
        
        return results, self.generator, generated_images


