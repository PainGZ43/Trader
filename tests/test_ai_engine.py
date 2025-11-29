import pytest
import pandas as pd
import numpy as np
import os
import joblib
from unittest.mock import MagicMock, patch
from strategy.ai_engine import AIEngine

# Mock Scikit-learn model
class MockSklearnModel:
    def predict_proba(self, X):
        # Return probability [0.4, 0.6] for all inputs
        return np.array([[0.4, 0.6]] * len(X))
        
    def predict(self, X):
        return np.array([0.6] * len(X))

@pytest.fixture
def ai_engine_instance():
    return AIEngine()

@pytest.fixture
def mock_model_path(tmp_path):
    model = MockSklearnModel()
    path = tmp_path / "test_model.pkl"
    joblib.dump(model, path)
    return str(path)

def test_load_sklearn_model(ai_engine_instance, mock_model_path):
    """Test loading a Scikit-learn model."""
    ai_engine_instance.load_model("test_model", mock_model_path)
    assert "test_model" in ai_engine_instance.models
    
def test_preprocess(ai_engine_instance):
    """Test preprocessing logic."""
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    ai_engine_instance.feature_configs["test_model"] = ['a', 'b']
    
    features = ai_engine_instance.preprocess(df, "test_model")
    assert features.shape == (2, 2)
    assert np.array_equal(features, [[1, 3], [2, 4]])
    
    # Test missing column
    ai_engine_instance.feature_configs["test_model"] = ['a', 'c']
    with pytest.raises(ValueError):
        ai_engine_instance.preprocess(df, "test_model")

def test_predict_sklearn(ai_engine_instance, mock_model_path):
    """Test inference with Scikit-learn model."""
    ai_engine_instance.load_model("test_model", mock_model_path)
    
    df = pd.DataFrame({'a': [1], 'b': [2]})
    # Mock feature config to avoid missing column error if we didn't set it
    # But preprocess uses all columns if no config.
    
    score = ai_engine_instance.predict(df, "test_model")
    assert score == 0.6

def test_predict_missing_model(ai_engine_instance):
    """Test prediction with unknown model."""
    score = ai_engine_instance.predict(pd.DataFrame(), "unknown")
    assert score == 0.0
