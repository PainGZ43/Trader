import os
import joblib
import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional
from core.logger import get_logger

# Optional imports for AI frameworks
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import sklearn
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class AIEngine:
    """
    AI Engine for managing models and performing inference.
    Supports PyTorch (.pt) and Scikit-learn (.pkl) models.
    """
    def __init__(self):
        self.logger = get_logger("AIEngine")
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.feature_configs: Dict[str, List[str]] = {}

    def load_model(self, model_name: str, model_path: str, scaler_path: Optional[str] = None, feature_config: Optional[List[str]] = None):
        """
        Load a model from disk.
        """
        if not os.path.exists(model_path):
            self.logger.error(f"Model file not found: {model_path}")
            return

        try:
            if model_path.endswith(".pt"):
                if not TORCH_AVAILABLE:
                    self.logger.error("PyTorch is not installed.")
                    return
                self.models[model_name] = torch.jit.load(model_path)
                self.models[model_name].eval()
                self.logger.info(f"Loaded PyTorch model: {model_name}")
                
            elif model_path.endswith(".pkl"):
                if not SKLEARN_AVAILABLE:
                    self.logger.error("Scikit-learn is not installed.")
                    return
                self.models[model_name] = joblib.load(model_path)
                self.logger.info(f"Loaded Scikit-learn model: {model_name}")
            else:
                self.logger.error(f"Unsupported model format: {model_path}")
                return

            # Load Scaler if provided
            if scaler_path and os.path.exists(scaler_path):
                self.scalers[model_name] = joblib.load(scaler_path)
                self.logger.info(f"Loaded Scaler for {model_name}")

            # Set Feature Config
            if feature_config:
                self.feature_configs[model_name] = feature_config

        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")

    def preprocess(self, df: pd.DataFrame, model_name: str) -> np.ndarray:
        """
        Preprocess data for inference.
        """
        if model_name not in self.feature_configs:
            self.logger.warning(f"No feature config for {model_name}. Using all columns.")
            features = df.values
        else:
            required_features = self.feature_configs[model_name]
            # Check if columns exist
            missing = [col for col in required_features if col not in df.columns]
            if missing:
                raise ValueError(f"Missing features: {missing}")
            features = df[required_features].values

        # Scale
        if model_name in self.scalers:
            scaler = self.scalers[model_name]
            features = scaler.transform(features)
            
        return features

    def predict(self, df: pd.DataFrame, model_name: str) -> float:
        """
        Perform inference and return prediction score (0.0 ~ 1.0).
        Assumes binary classification (Up/Down) or regression.
        """
        if model_name not in self.models:
            self.logger.error(f"Model {model_name} not loaded.")
            return 0.0

        try:
            model = self.models[model_name]
            input_data = self.preprocess(df, model_name)
            
            # Inference
            if isinstance(model, torch.jit.ScriptModule) or (TORCH_AVAILABLE and isinstance(model, torch.nn.Module)):
                with torch.no_grad():
                    tensor_input = torch.tensor(input_data, dtype=torch.float32)
                    output = model(tensor_input)
                    # Assuming output is probability or logit
                    if output.shape[1] == 1:
                        return float(torch.sigmoid(output).item())
                    else:
                        return float(torch.softmax(output, dim=1)[0][1].item()) # Prob of class 1
            
            elif hasattr(model, "predict_proba"):
                # Scikit-learn Classifier
                prob = model.predict_proba(input_data)
                return float(prob[0][1]) # Prob of class 1
            
            elif hasattr(model, "predict"):
                # Scikit-learn Regressor
                return float(model.predict(input_data)[0])
            
            else:
                self.logger.error(f"Unknown model type for {model_name}")
                return 0.0

        except Exception as e:
            self.logger.error(f"Inference failed for {model_name}: {e}")
            return 0.0

ai_engine = AIEngine()
