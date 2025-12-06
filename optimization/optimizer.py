import itertools
import pandas as pd
from typing import Dict, Any, List, Type
from concurrent.futures import ProcessPoolExecutor, as_completed
from strategy.base_strategy import BaseStrategy
from strategy.backtester import EventDrivenBacktester as Backtester
from core.logger import get_logger

class Optimizer:
    """
    Strategy Optimizer using Grid Search.
    """
    def __init__(self):
        self.logger = get_logger("Optimizer")

    def generate_grid(self, param_ranges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """
        Generate all combinations of parameters.
        param_ranges: {"k": [0.1, 0.2, 0.3], "window": [5, 10]}
        Returns: [{"k": 0.1, "window": 5}, {"k": 0.1, "window": 10}, ...]
        """
        keys = param_ranges.keys()
        values = param_ranges.values()
        combinations = list(itertools.product(*values))
        
        grid = []
        for combo in combinations:
            grid.append(dict(zip(keys, combo)))
            
        return grid

    def run_optimization(self, 
                         strategy_cls: Type[BaseStrategy], 
                         df: pd.DataFrame, 
                         param_ranges: Dict[str, List[Any]],
                         initial_capital: float = 10000000,
                         commission: float = 0.00015,
                         slippage: float = 0.0005,
                         max_workers: int = 4) -> pd.DataFrame:
        """
        Run optimization using Grid Search.
        """
        grid = self.generate_grid(param_ranges)
        self.logger.info(f"Starting optimization for {strategy_cls.get_name()}. Total combinations: {len(grid)}")
        
        results = []
        
        # Helper function for parallel execution
        # Note: This must be picklable, so it might be better defined outside or as static
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._run_single_backtest, 
                    strategy_cls, 
                    df, 
                    params, 
                    initial_capital, 
                    commission, 
                    slippage
                ): params for params in grid
            }
            
            for future in as_completed(futures):
                params = futures[future]
                try:
                    metrics = future.result()
                    # Flatten metrics and params
                    result = {**params, **metrics}
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Optimization failed for params {params}: {e}")
                    
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            # Sort by Total Return
            if 'total_return' in results_df.columns:
                results_df = results_df.sort_values(by='total_return', ascending=False)
                
        return results_df

    @staticmethod
    def _run_single_backtest(strategy_cls, df, params, initial_capital, commission, slippage):
        """
        Static method for single backtest run (picklable).
        """
        # Initialize strategy with params
        # Note: Strategy ID and Symbol are dummy here as we reuse logic
        strategy = strategy_cls("OPT_TEST", "Unknown")
        strategy.initialize(params)
        
        backtester = Backtester()
        backtester.configure({
            "initial_capital": initial_capital,
            "commission_rate": commission,
            "slippage_rate": slippage
        })
        result = backtester.run(strategy, df)
        
        # Return only metrics to save memory
        return {
            "total_return": result.total_return,
            "final_capital": result.final_capital,
            "mdd": result.mdd,
            "win_rate": result.win_rate,
            "sharpe_ratio": result.sharpe_ratio,
            "sortino_ratio": result.sortino_ratio,
            "trades": len(result.trades)
        }
