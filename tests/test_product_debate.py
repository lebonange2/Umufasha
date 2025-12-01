"""Tests for product debate system."""
import pytest
import numpy as np
from app.product_debate.models import (
    FeatureVector, DeviationProposal, ConceptOnePager, ProposalStatus
)
from app.product_debate.scoring import NoveltyScorer, check_go_threshold


def test_feature_vector():
    """Test FeatureVector model."""
    fv = FeatureVector(
        functional_attributes=["battery", "portable"],
        target_user="consumer",
        price_band="$50-100",
        channel="Amazon",
        materials=["plastic", "electronics"],
        regulations=["FCC"],
        pain_points=["weight"]
    )
    
    assert fv.target_user == "consumer"
    assert len(fv.functional_attributes) == 2
    
    # Test serialization
    data = fv.to_dict()
    fv2 = FeatureVector.from_dict(data)
    assert fv2.target_user == fv.target_user


def test_novelty_scorer():
    """Test NoveltyScorer."""
    known_products = [
        {
            "name": "Product 1",
            "functional_attributes": ["battery", "portable"],
            "target_user": "consumer",
            "price_band": "$50-100",
            "channel": "Amazon",
            "materials": ["plastic"],
            "regulations": ["FCC"],
            "pain_points": []
        },
        {
            "name": "Product 2",
            "functional_attributes": ["battery", "solar"],
            "target_user": "consumer",
            "price_band": "$100-200",
            "channel": "DTC",
            "materials": ["plastic", "solar panel"],
            "regulations": ["FCC"],
            "pain_points": []
        }
    ]
    
    scorer = NoveltyScorer(known_products)
    
    # Test centroid calculation
    assert scorer.centroid is not None
    assert len(scorer.centroid) > 0
    
    # Test novelty calculation
    proposal_fv = FeatureVector(
        functional_attributes=["battery", "portable", "wireless"],
        target_user="consumer",
        price_band="$75-125",
        channel="Amazon",
        materials=["plastic", "electronics"],
        regulations=["FCC"],
        pain_points=[]
    )
    
    sigma = scorer.calculate_novelty_sigma(proposal_fv)
    assert isinstance(sigma, float)
    assert sigma >= 0


def test_composite_score():
    """Test composite score calculation."""
    known_products = [
        {
            "name": "Product 1",
            "functional_attributes": ["battery"],
            "target_user": "consumer",
            "price_band": "$50",
            "channel": "Amazon",
            "materials": [],
            "regulations": [],
            "pain_points": []
        }
    ]
    
    scorer = NoveltyScorer(known_products)
    
    proposal = DeviationProposal(
        id="test-1",
        name="Test Product",
        description="Test",
        feature_vector=FeatureVector(
            functional_attributes=["battery"],
            target_user="consumer",
            price_band="$50",
            channel="Amazon",
            materials=[],
            regulations=[],
            pain_points=[]
        ),
        user_value=8.0,
        novelty_sigma=0.75,
        complexity=5.0
    )
    
    score = scorer.calculate_composite_score(proposal)
    assert isinstance(score, float)
    assert 0 <= score <= 10


def test_go_threshold():
    """Test Go Threshold check."""
    proposal = DeviationProposal(
        id="test-1",
        name="Test",
        description="Test",
        feature_vector=FeatureVector(),
        user_value=8.0,
        novelty_sigma=0.75,
        complexity=5.0,
        composite_score=8.0
    )
    
    concept = ConceptOnePager(
        name="Test Product",
        user_story="Test story",
        top_features=["feature1"],
        bom={"component1": 10.0},
        unit_cost=25.0,
        target_msrp=50.0,
        gross_margin=50.0,
        supply_notes="Test",
        compliance_path="Test",
        pilot_channel="DTC",
        first_run_moqs={"component1": 500},
        risks=[]
    )
    
    # Should pass: composite >= 7.5 and margin >= 45%
    assert check_go_threshold(proposal, concept) == True
    
    # Should fail: margin too low
    concept_low_margin = ConceptOnePager(
        name="Test",
        user_story="Test",
        top_features=[],
        bom={},
        unit_cost=30.0,
        target_msrp=50.0,
        gross_margin=40.0,  # Below 45%
        supply_notes="",
        compliance_path="",
        pilot_channel="",
        first_run_moqs={},
        risks=[]
    )
    assert check_go_threshold(proposal, concept_low_margin) == False
    
    # Should fail: composite score too low
    proposal_low_score = DeviationProposal(
        id="test-2",
        name="Test",
        description="Test",
        feature_vector=FeatureVector(),
        user_value=5.0,
        novelty_sigma=0.5,
        complexity=8.0,
        composite_score=6.0  # Below 7.5
    )
    assert check_go_threshold(proposal_low_score, concept) == False


def test_price_band_parsing():
    """Test price band parsing in NoveltyScorer."""
    known_products = [
        {
            "name": "Product 1",
            "functional_attributes": [],
            "target_user": "consumer",
            "price_band": "$50-100",
            "channel": "Amazon",
            "materials": [],
            "regulations": [],
            "pain_points": []
        }
    ]
    
    scorer = NoveltyScorer(known_products)
    
    # Test parsing
    assert scorer._parse_price_band("$50-100") == 75.0
    assert scorer._parse_price_band("$100") == 100.0
    assert scorer._parse_price_band("") == 0.0

