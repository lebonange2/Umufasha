"""Deduplication logic for ideas using semantic similarity."""
from typing import List, Tuple, Optional
import numpy as np
from utils.logging import get_logger

logger = get_logger('dedupe')


class Deduplicator:
    """Handles deduplication of ideas using semantic similarity."""
    
    def __init__(self, threshold: float = 0.85, use_embeddings: bool = True):
        """Initialize deduplicator.
        
        Args:
            threshold: Similarity threshold (0.0-1.0) for considering duplicates
            use_embeddings: Use sentence transformers if available, else fallback to LLM
        """
        self.threshold = threshold
        self.use_embeddings = use_embeddings
        self.model = None
        
        if use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence-transformers model for deduplication")
            except ImportError:
                logger.warning("sentence-transformers not available, will use LLM-based deduplication")
                self.use_embeddings = False
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0-1.0)
        """
        if not self.model:
            # Fallback to simple token overlap
            return self._token_overlap_similarity(text1, text2)
        
        # Use embeddings
        embeddings = self.model.encode([text1, text2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)
    
    def _token_overlap_similarity(self, text1: str, text2: str) -> float:
        """Fallback similarity using token overlap (Jaccard)."""
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)
    
    def find_duplicates(self, texts: List[str]) -> List[Tuple[int, int, float]]:
        """Find duplicate pairs in a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of (index1, index2, similarity) tuples for duplicates
        """
        duplicates = []
        
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = self.compute_similarity(texts[i], texts[j])
                if similarity >= self.threshold:
                    duplicates.append((i, j, similarity))
        
        return duplicates
    
    def find_similar(self, query: str, texts: List[str], top_k: int = 5) -> List[Tuple[int, float]]:
        """Find most similar texts to a query.
        
        Args:
            query: Query text
            texts: List of candidate texts
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity) tuples, sorted by similarity
        """
        similarities = []
        
        for i, text in enumerate(texts):
            similarity = self.compute_similarity(query, text)
            similarities.append((i, similarity))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def batch_encode(self, texts: List[str]) -> Optional[np.ndarray]:
        """Batch encode texts to embeddings for efficient similarity computation.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Numpy array of embeddings or None if model not available
        """
        if not self.model:
            return None
        
        return self.model.encode(texts)
    
    def compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """Compute pairwise similarity matrix from embeddings.
        
        Args:
            embeddings: Array of embeddings (n_samples, embedding_dim)
            
        Returns:
            Similarity matrix (n_samples, n_samples)
        """
        # Normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / norms
        
        # Compute cosine similarity matrix
        similarity_matrix = np.dot(normalized, normalized.T)
        
        return similarity_matrix
