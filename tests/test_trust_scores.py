"""
Tests for Trust Score computation.
"""

import pytest
from models.trust_score import TrustScore, TrustSignals, TrustLabel
from trust.score_engine import TrustScoreEngine

def test_trust_score_perfect():
    """Test trust score with perfect signals."""
    engine = TrustScoreEngine()
    signals = TrustSignals(
        documentation=1.0,
        freshness=1.0,
        ownership=1.0,
        test_coverage=1.0,
        usage=1.0
    )
    score = engine.compute_score("test-id", signals)
    
    assert score.score == 1.0
    assert score.label == TrustLabel.TRUSTED

def test_trust_score_poor():
    """Test trust score with poor signals."""
    engine = TrustScoreEngine()
    signals = TrustSignals(
        documentation=0.0,
        freshness=0.0,
        ownership=0.0,
        test_coverage=0.0,
        usage=0.0
    )
    score = engine.compute_score("test-id", signals)
    
    assert score.score == 0.0
    assert score.label == TrustLabel.UNKNOWN

def test_trust_score_mixed():
    """Test trust score with mixed signals."""
    engine = TrustScoreEngine()
    signals = TrustSignals(
        documentation=1.0, # 0.25
        freshness=0.5,     # 0.15
        ownership=1.0,     # 0.20
        test_coverage=0.0, # 0.0
        usage=0.5          # 0.05
    )                      # Total: 0.65
    score = engine.compute_score("test-id", signals)
    
    assert score.score == 0.65
    assert score.label == TrustLabel.REVIEW
