import pandas as pd
from typing import Dict, Any, Optional
from strategy.base_strategy import BaseStrategy, Signal
from strategy.ai_engine import ai_engine
from strategy.strategies import RSIStrategy

class HybridStrategy(BaseStrategy):
    """
    Hybrid Strategy: Technical Indicator (RSI) + AI Prediction.
    Buy if RSI < 30 AND AI Score > 0.6
    """
    def __init__(self, strategy_id: str, symbol: str):
        super().__init__(strategy_id, symbol)
        self.rsi_strategy = RSIStrategy(strategy_id + "_rsi", symbol)
        self.model_name = "price_predictor"
        self.ai_threshold = 0.6

    def initialize(self, config: Dict[str, Any]):
        super().initialize(config)
        self.rsi_strategy.initialize(config)
        self.model_name = config.get("model_name", "price_predictor")
        self.ai_threshold = config.get("ai_threshold", 0.6)
        
        # Load Model (In real app, model path should be in config)
        model_path = config.get("model_path")
        if model_path:
            ai_engine.load_model(self.model_name, model_path)

    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Get Technical Signals
        df = self.rsi_strategy.calculate_signals(df)
        
        # 2. Get AI Predictions (Batch Inference)
        # Note: In backtesting, we might need a way to batch predict efficiently.
        # For simplicity here, we assume AI prediction is added as a column or we iterate.
        # Iterating row by row is slow for backtesting.
        # Ideally, AIEngine supports batch prediction.
        
        # Let's assume we have a 'ai_score' column pre-calculated or we calculate it here.
        # For demonstration, we'll simulate AI score if not present.
        if 'ai_score' not in df.columns:
            # In real scenario, we would call ai_engine.predict(df) but that expects single input usually for realtime.
            # For backtest, we need batch_predict.
            # Let's just use a placeholder logic for now or skip AI in backtest if model not loaded.
            df['ai_score'] = 0.5 
        
        # 3. Combine
        # Buy: RSI Buy Signal (1) AND AI Score > Threshold
        df['final_signal'] = 0
        df.loc[(df['signal'] == 1) & (df['ai_score'] > self.ai_threshold), 'final_signal'] = 1
        df.loc[(df['signal'] == -1), 'final_signal'] = -1 # Sell signal usually doesn't need AI confirmation (Risk management)
        
        # Rename for consistency
        df['signal'] = df['final_signal']
        return df

    async def on_realtime_data(self, data: Dict[str, Any]) -> Optional[Signal]:
        # 1. Get Technical Signal
        # We need a way to get the latest DF from data collector or maintain it.
        # Assuming we can get the latest indicators or DF.
        # For now, let's assume we have access to the latest candle.
        
        # Placeholder for realtime logic
        # rsi_signal = ...
        
        # 2. Get AI Prediction
        # input_features = ...
        # ai_score = ai_engine.predict(input_features, self.model_name)
        
        # 3. Combine
        # if rsi_signal == 1 and ai_score > self.ai_threshold:
        #     return Signal(...)
        
        return None
