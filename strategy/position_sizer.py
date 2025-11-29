from typing import Dict, Any
import math

class PositionSizer:
    """
    Calculates position size based on risk management rules.
    """
    def __init__(self):
        # Default Settings
        self.risk_per_trade = 0.01 # 1% of capital
        self.max_position_size = 0.1 # Max 10% of capital per trade
        self.min_trade_amt = 10000 # Min trade amount (KRW)

    def configure(self, config: Dict[str, Any]):
        self.risk_per_trade = config.get("risk_per_trade", 0.01)
        self.max_position_size = config.get("max_position_size", 0.1)

    def calculate_size(self, capital: float, entry_price: float, stop_loss: float, win_rate: float = 0.5, risk_reward_ratio: float = 2.0, method: str = "risk_based") -> int:
        """
        Calculate number of shares to buy/sell.
        """
        if capital <= 0 or entry_price <= 0:
            return 0

        # 1. Calculate Risk Amount (Capital * Risk%)
        risk_amt = capital * self.risk_per_trade
        
        # 2. Calculate Risk Per Share
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            # If no stop loss defined, assume some default risk or fallback
            # Fallback to fixed fractional of capital
            position_amt = capital * self.max_position_size
            return int(position_amt / entry_price)

        # 3. Calculate Size based on Method
        if method == "kelly":
            # Kelly Criterion: f = (bp - q) / b
            # b = risk_reward_ratio
            # p = win_rate
            # q = 1 - p
            b = risk_reward_ratio
            p = win_rate
            q = 1 - p
            
            if b == 0:
                f = 0
            else:
                f = (b * p - q) / b
            
            # Half Kelly for safety
            f = f * 0.5
            
            if f <= 0:
                return 0
                
            position_amt = capital * f
            
        else: # "risk_based" (Default)
            # Size = Risk Amount / Risk Per Share
            size_by_risk = risk_amt / risk_per_share
            position_amt = size_by_risk * entry_price

        # 4. Apply Constraints
        # Max Position Size Cap
        max_amt = capital * self.max_position_size
        if position_amt > max_amt:
            position_amt = max_amt
            
        # Min Trade Amount
        if position_amt < self.min_trade_amt:
            return 0
            
        # Convert to number of shares
        shares = int(position_amt / entry_price)
        return shares
