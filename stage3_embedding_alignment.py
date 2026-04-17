"""
Stage 3: Cross-Architectural Embedding Alignment
Project embeddings to shared space and analyze alignment
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from pathlib import Path
import seaborn as sns

class Stage3EmbeddingAlignment:
    """Stage 3: Cross-Architectural Embedding Alignment"""
    
    def __init__(self, embeddings_dict, image_paths, labels, classes, output_dir):
        self.embeddings = embeddings_dict
        self.image_paths = image_paths
        self.labels = labels
        self.classes = classes
        self.output_dir = Path(output_dir)
    
    def project_to_shared_space(self, method='tsne', dim=2):
        """Project all embeddings to shared low-dimensional space"""
        print(f"   Projecting embeddings to {dim}D space using {method}...")
        
        # Collect all embeddings
        all_embeddings = []
        embedding_names = []
        
        for name, emb in self.embeddings.items():
            if emb is not None:
                all_embeddings.append(emb)
                embedding_names.extend([name] * len(emb))
        
        if not all_embeddings:
            print("   ⚠️ No embeddings available")
            return None
        
        # Concatenate
        combined_embeddings = np.concatenate(all_embeddings, axis=0)
        
        # Normalize
        combined_embeddings = combined_embeddings / (np.linalg.norm(combined_embeddings, axis=1, keepdims=True) + 1e-8)
        
        # Project
        if method == 'tsne':
            projector = TSNE(n_components=dim, random_state=42, perplexity=min(30, len(combined_embeddings)-1))
        else:
            projector = PCA(n_components=dim)
        
        projected = projector.fit_transform(combined_embeddings)
        
        return projected, embedding_names
    
    def analyze_cluster_alignment(self, projected, embedding_names):
        """Analyze cluster alignment across models"""
        print("   Analyzing cluster alignment...")
        
        # Separate by model - handle case where embeddings might be different lengths
        vit_indices = []
        swin_indices = []
        clip_indices = []
        
        current_idx = 0
        for model_name in ['vit', 'swin', 'clip']:
            if model_name in self.embeddings and self.embeddings[model_name] is not None:
                num_emb = len(self.embeddings[model_name])
                if model_name == 'vit':
                    vit_indices = list(range(current_idx, current_idx + num_emb))
                elif model_name == 'swin':
                    swin_indices = list(range(current_idx, current_idx + num_emb))
                elif model_name == 'clip':
                    clip_indices = list(range(current_idx, current_idx + num_emb))
                current_idx += num_emb
        
        alignment_metrics = {
            'vit_swin_correlation': 0.0,
            'vit_clip_correlation': 0.0,
            'swin_clip_correlation': 0.0
        }
        
        # Compute pairwise correlations in embedding space
        if len(vit_indices) > 0 and len(swin_indices) > 0:
            vit_emb = projected[vit_indices]
            swin_emb = projected[swin_indices]
            # Use first few samples for comparison
            min_len = min(len(vit_emb), len(swin_emb))
            if min_len > 0:
                correlation = np.corrcoef(
                    vit_emb[:min_len].flatten(),
                    swin_emb[:min_len].flatten()
                )[0, 1]
                alignment_metrics['vit_swin_correlation'] = float(correlation) if not np.isnan(correlation) else 0.0
        
        return alignment_metrics
    
    def analyze_semantic_separation(self, projected, embedding_names):
        """Analyze semantic concept separation"""
        print("   Analyzing semantic separation...")
        
        # Group by class labels
        class_separations = {}
        
        for class_idx, class_name in enumerate(self.classes):
            # Find indices for this class
            class_indices = [i for i, label in enumerate(self.labels) if label == class_idx]
            
            if len(class_indices) > 0:
                # Get embeddings for this class across all models
                class_embeddings = []
                for idx in class_indices:
                    # Find corresponding embedding indices
                    for model_name in ['vit', 'swin', 'clip']:
                        if model_name in self.embeddings and self.embeddings[model_name] is not None:
                            model_start = sum(len(self.embeddings[m]) for m in ['vit', 'swin', 'clip'] if m in self.embeddings and m < model_name)
                            emb_idx = model_start + idx
                            if emb_idx < len(projected):
                                class_embeddings.append(projected[emb_idx])
                
                if len(class_embeddings) > 0:
                    class_embeddings = np.array(class_embeddings)
                    # Compute intra-class variance
                    variance = np.var(class_embeddings, axis=0).mean()
                    class_separations[class_name] = float(variance)
        
        return class_separations
    
    def identify_model_disagreements(self, projected, embedding_names):
        """Identify regions where models disagree"""
        print("   Identifying model disagreements...")
        
        disagreements = []
        
        # For each image, compare embeddings across models
        for img_idx in range(len(self.image_paths)):
            vit_emb = None
            swin_emb = None
            clip_emb = None
            
            # Find embeddings for this image
            vit_start = 0
            if 'vit' in self.embeddings and self.embeddings['vit'] is not None:
                if img_idx < len(self.embeddings['vit']):
                    vit_emb = projected[vit_start + img_idx]
            
            swin_start = len(self.embeddings.get('vit', [])) if 'vit' in self.embeddings else 0
            if 'swin' in self.embeddings and self.embeddings['swin'] is not None:
                if img_idx < len(self.embeddings['swin']):
                    swin_emb = projected[swin_start + img_idx]
            
            clip_start = swin_start + (len(self.embeddings.get('swin', [])) if 'swin' in self.embeddings else 0)
            if 'clip' in self.embeddings and self.embeddings['clip'] is not None:
                if img_idx < len(self.embeddings['clip']):
                    clip_emb = projected[clip_start + img_idx]
            
            # Compute pairwise distances
            distances = {}
            if vit_emb is not None and swin_emb is not None:
                distances['vit_swin'] = float(np.linalg.norm(vit_emb - swin_emb))
            if vit_emb is not None and clip_emb is not None:
                distances['vit_clip'] = float(np.linalg.norm(vit_emb - clip_emb))
            if swin_emb is not None and clip_emb is not None:
                distances['swin_clip'] = float(np.linalg.norm(swin_emb - clip_emb))
            
            if distances:
                max_distance = max(distances.values())
                if max_distance > np.percentile(list(distances.values()), 75):
                    disagreements.append({
                        'image_idx': img_idx,
                        'distances': distances,
                        'class': self.classes[self.labels[img_idx]]
                    })
        
        return disagreements
    
    def visualize_embeddings(self, projected, embedding_names):
        """Create visualization of embeddings"""
        print("   Creating embedding visualization...")
        
        if projected.shape[1] < 2:
            print("   ⚠️ Cannot visualize: insufficient dimensions")
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: By model
        ax1 = axes[0]
        colors = {'vit': 'red', 'swin': 'blue', 'clip': 'green'}
        for model_name in ['vit', 'swin', 'clip']:
            indices = [i for i, name in enumerate(embedding_names) if name == model_name]
            if indices:
                ax1.scatter(projected[indices, 0], projected[indices, 1], 
                           c=colors.get(model_name, 'gray'), 
                           label=model_name.upper(), alpha=0.6, s=50)
        ax1.set_title('Embeddings by Model Architecture')
        ax1.set_xlabel('Dimension 1')
        ax1.set_ylabel('Dimension 2')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: By class
        ax2 = axes[1]
        unique_labels = list(set(self.labels))
        colors_map = plt.cm.tab20(np.linspace(0, 1, len(unique_labels)))
        
        for i, label in enumerate(unique_labels):
            # Find all embeddings for this label
            label_indices = []
            for img_idx, img_label in enumerate(self.labels):
                if img_label == label:
                    # Find corresponding embedding indices
                    for model_name in ['vit', 'swin', 'clip']:
                        if model_name in embedding_names:
                            model_start = sum(len(self.embeddings.get(m, [])) for m in ['vit', 'swin', 'clip'] if m in self.embeddings and m < model_name)
                            emb_idx = model_start + img_idx
                            if emb_idx < len(projected):
                                label_indices.append(emb_idx)
            
            if label_indices:
                ax2.scatter(projected[label_indices, 0], projected[label_indices, 1],
                           c=[colors_map[i]], label=self.classes[label], alpha=0.6, s=50)
        
        ax2.set_title('Embeddings by Semantic Class')
        ax2.set_xlabel('Dimension 1')
        ax2.set_ylabel('Dimension 2')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "embedding_visualization.png", dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"   ✅ Visualization saved to {self.output_dir / 'embedding_visualization.png'}")
    
    def run(self):
        """Execute Stage 3"""
        # Project to shared space
        projected, embedding_names = self.project_to_shared_space(method='tsne', dim=2)
        
        if projected is None:
            return {}
        
        # Analyze cluster alignment
        alignment_metrics = self.analyze_cluster_alignment(projected, embedding_names)
        
        # Analyze semantic separation
        semantic_separation = self.analyze_semantic_separation(projected, embedding_names)
        
        # Identify disagreements
        disagreements = self.identify_model_disagreements(projected, embedding_names)
        
        # Visualize
        self.visualize_embeddings(projected, embedding_names)
        
        # Compile results
        results = {
            'cluster_alignment': alignment_metrics,
            'semantic_separation': semantic_separation,
            'model_disagreements': disagreements[:10],  # Top 10
            'num_disagreements': len(disagreements)
        }
        
        print(f"\n   ✅ Embedding alignment analysis complete")
        print(f"   ✅ Found {len(disagreements)} model disagreements")
        
        return results

