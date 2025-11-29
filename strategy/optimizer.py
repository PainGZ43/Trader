import itertools
import pandas as pd
from typing import Dict, Any, List, Type
from strategy.base_strategy import StrategyInterface
from strategy.backtester import EventDrivenBacktester
from core.logger import get_logger

class StrategyOptimizer:
    """
    Optimizes strategy parameters using Grid Search.
    """
    def __init__(self):
        self.logger = get_logger("Optimizer")
        self.backtester = EventDrivenBacktester()

    def grid_search(self, strategy_cls: Type[StrategyInterface], param_grid: Dict[str, List[Any]], data: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform Grid Search.
        param_grid: {'k': [0.4, 0.5, 0.6], 'window': [10, 20]}
        """
        keys, values = zip(*param_grid.items())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        best_result = None
        best_params = None
        best_score = -float('inf') # Optimize for Total Return
        
        self.logger.info(f"Starting Grid Search with {len(combinations)} combinations...")
        
        for params in combinations:
            # Create Strategy Instance
            strategy = strategy_cls("optim_temp", "005930")
            strategy.initialize(params)
            
            # Run Backtest
            result = self.backtester.run(strategy, data)
            
            # Score (Total Return)
            score = result.total_return
            
            if score > best_score:
                best_score = score
                best_params = params
                best_result = result
                
        self.logger.info(f"Optimization Finished. Best Score: {best_score:.2f}%")
        self.logger.info(f"Best Params: {best_params}")
        
        return {
            "best_params": best_params,
            "best_score": best_score,
            "best_result": best_result
        }
