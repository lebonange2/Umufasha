"""Novelty scoring and composite score calculation."""
import numpy as np
from typing import List, Dict, Any
from app.product_debate.models import FeatureVector, DeviationProposal


class NoveltyScorer:
    """Calculate novelty scores using feature vector distances."""
    
    def __init__(self, known_products: List[Dict[str, Any]]):
        """Initialize with known products.
        
        Args:
            known_products: List of known products with feature vectors
        """
        self.known_products = known_products
        self.feature_vectors = [self._vectorize(p) for p in known_products]
        if self.feature_vectors:
            self.centroid = self._calculate_centroid()
            self.std_dev = self._calculate_std_dev()
        else:
            self.centroid = None
            self.std_dev = None
    
    def _vectorize(self, product: Dict[str, Any]) -> np.ndarray:
        """Convert product to numerical feature vector.
        
        Uses a simple rule-based approach:
        - Functional attributes: binary encoding of common features
        - Target user: categorical encoding
        - Price band: numerical (midpoint of range)
        - Channel: categorical encoding
        - Materials: binary encoding
        - Regulations: binary encoding
        - Pain points: binary encoding
        """
        # Collect all unique features across known products
        all_attrs = set()
        all_materials = set()
        all_regulations = set()
        all_pain_points = set()
        
        for p in self.known_products:
            if isinstance(p, dict):
                all_attrs.update(p.get("functional_attributes", []))
                all_materials.update(p.get("materials", []))
                all_regulations.update(p.get("regulations", []))
                all_pain_points.update(p.get("pain_points", []))
        
        # Convert to sorted lists for consistent indexing
        all_attrs = sorted(list(all_attrs))
        all_materials = sorted(list(all_materials))
        all_regulations = sorted(list(all_regulations))
        all_pain_points = sorted(list(all_pain_points))
        
        # Build feature vector
        features = []
        
        # Functional attributes (binary)
        attrs = product.get("functional_attributes", [])
        features.extend([1 if attr in attrs else 0 for attr in all_attrs])
        
        # Target user (one-hot encoding of common categories)
        user_categories = ["consumer", "professional", "enterprise", "hobbyist", "student"]
        user = product.get("target_user", "").lower()
        features.extend([1 if cat in user else 0 for cat in user_categories])
        
        # Price band (numerical - midpoint)
        price_band = product.get("price_band", "")
        price_val = self._parse_price_band(price_band)
        features.append(price_val)
        
        # Channel (one-hot)
        channel_categories = ["dtc", "amazon", "b2b", "retail", "wholesale"]
        channel = product.get("channel", "").lower()
        features.extend([1 if cat in channel else 0 for cat in channel_categories])
        
        # Materials (binary)
        materials = product.get("materials", [])
        features.extend([1 if mat in materials else 0 for mat in all_materials])
        
        # Regulations (binary)
        regulations = product.get("regulations", [])
        features.extend([1 if reg in regulations else 0 for reg in all_regulations])
        
        # Pain points (binary)
        pain_points = product.get("pain_points", [])
        features.extend([1 if pp in pain_points else 0 for pp in all_pain_points])
        
        return np.array(features, dtype=float)
    
    def _parse_price_band(self, price_band: str) -> float:
        """Parse price band string to numerical value."""
        if not price_band:
            return 0.0
        
        # Remove $ and commas
        price_band = price_band.replace("$", "").replace(",", "").strip()
        
        # Try to extract range
        if "-" in price_band:
            parts = price_band.split("-")
            try:
                low = float(parts[0].strip())
                high = float(parts[1].strip())
                return (low + high) / 2
            except ValueError:
                pass
        
        # Try single value
        try:
            return float(price_band)
        except ValueError:
            return 0.0
    
    def _calculate_centroid(self) -> np.ndarray:
        """Calculate centroid of known products."""
        if not self.feature_vectors:
            return np.array([])
        return np.mean(self.feature_vectors, axis=0)
    
    def _calculate_std_dev(self) -> float:
        """Calculate standard deviation of distances from centroid."""
        if not self.feature_vectors or len(self.feature_vectors) < 2:
            return 1.0
        
        distances = [np.linalg.norm(vec - self.centroid) for vec in self.feature_vectors]
        return np.std(distances) if distances else 1.0
    
    def calculate_novelty_sigma(self, proposal: FeatureVector) -> float:
        """Calculate novelty as sigma distance from centroid.
        
        Args:
            proposal: Feature vector of the proposal
            
        Returns:
            Sigma distance (z-score)
        """
        if self.centroid is None or self.std_dev == 0:
            return 0.5  # Default to target range
        
        proposal_vec = self._vectorize(proposal.to_dict())
        
        # Calculate distance from centroid
        distance = np.linalg.norm(proposal_vec - self.centroid)
        
        # Convert to z-score (sigma)
        sigma = distance / self.std_dev if self.std_dev > 0 else 0.5
        
        return sigma
    
    def calculate_composite_score(self, proposal: DeviationProposal) -> float:
        """Calculate composite score for a proposal.
        
        Formula: 0.4*UserValue + 0.3*(1-Complexity/10) + 0.3*(1-|σ-0.75|)
        
        Args:
            proposal: Deviation proposal
            
        Returns:
            Composite score (0-10)
        """
        user_value_score = proposal.user_value / 10.0  # Normalize to 0-1
        complexity_score = 1.0 - (proposal.complexity / 10.0)  # Lower complexity is better
        novelty_score = 1.0 - abs(proposal.novelty_sigma - 0.75)  # Target 0.75 sigma
        
        composite = (
            0.4 * user_value_score +
            0.3 * complexity_score +
            0.3 * novelty_score
        )
        
        return composite * 10.0  # Scale to 0-10


def check_go_threshold(proposal: DeviationProposal, concept: Any) -> bool:
    """Check if a concept meets the Go Threshold.
    
    Go Threshold: Composite ≥ 7.5/10 and margin ≥ 45% at target MSRP
    
    Args:
        proposal: Deviation proposal
        concept: ConceptOnePager
        
    Returns:
        True if threshold is met
    """
    if proposal.composite_score is None:
        return False
    
    if proposal.composite_score < 7.5:
        return False
    
    if concept is None:
        return False
    
    if concept.gross_margin < 45.0:
        return False
    
    return True

