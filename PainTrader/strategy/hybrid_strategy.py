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
        """
        Real-time signal generation.
        """
        try:
            from data.data_collector import data_collector
            from strategy.market_regime import MarketRegime
            
            # 1. Get Data
            df = await data_collector.get_recent_data(self.symbol, limit=100)
            if df.empty or len(df) < 60:
                return None
                
            # 2. Detect Market Regime
            regime_info = self.market_regime_detector.detect(df)
            regime = regime_info['regime']
            
            # Filter: Do not buy in Bear market
            if regime == MarketRegime.BEAR:
                return None
                
            # 3. Technical Analysis (RSI)
            # We need to calculate RSI on this DF
            # Using RSIStrategy's logic or direct calculation
            # For simplicity, let's use the indicator engine directly or the rsi_strategy if it exposes a method
            # rsi_strategy.calculate_signals works on DF.
            
            df = self.rsi_strategy.calculate_signals(df)
            last_signal = df['signal'].iloc[-1]
            
            if last_signal != 1: # Only interested in Buy for now
                return None
                
            # 4. AI Prediction (Mock for now, or real if engine ready)
            # ai_score = await ai_engine.predict_async(df) 
            ai_score = 0.7 # Mock
            
            if ai_score > self.ai_threshold:
                return Signal(
                    symbol=self.symbol,
                    type="BUY",
                    price=df['close'].iloc[-1],
                    timestamp=datetime.now(),
                    reason=f"RSI Buy + AI Score {ai_score:.2f} + Regime {regime.value}",
                    score=ai_score
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error in on_realtime_data: {e}")
            return None
