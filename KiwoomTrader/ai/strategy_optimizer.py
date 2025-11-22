import itertools
import matplotlib
matplotlib.use('Agg') # Force Agg backend
from logger import logger
from ai.backtester import Backtester

class StrategyOptimizer:
    """전략 파라미터 최적화 클래스"""
    
    def __init__(self):
        self.best_params = None
        self.best_result = None
        self.all_results = []
    
    def optimize(self, code, start_date, end_date, progress_callback=None):
        """
        여러 파라미터 조합을 테스트하여 최적의 전략을 찾습니다.
        """
        logger.info("전략 최적화 시작...")
        
        # 파라미터 그리드 정의
        # 파라미터 그리드 정의 (보수적 옵션 추가)
        param_grid = {
            'vol_multiplier': [2.0, 3.0, 5.0],
            'ai_threshold': [0.7, 0.8, 0.9],
            'rsi_threshold': [50, 60, 70],
            'take_profit': [0.5, 1.0, 2.0, 3.0],
            'stop_loss': [0.5, 1.0, 2.0],
            'time_exit': [5, 10, 30],
            'cooldown': [10, 30, 60]
        }
        
        # 모든 조합 생성
        keys = list(param_grid.keys())
        values = [param_grid[k] for k in keys]
        combinations = list(itertools.product(*values))
        
        total_combinations = len(combinations)
        logger.info(f"총 {total_combinations}개 조합 테스트 예정")
        
        best_score = -float('inf')
        self.all_results = []
        
        backtester = Backtester()
        
        for idx, combo in enumerate(combinations):
            params = dict(zip(keys, combo))
            
            # 진행률 업데이트
            if progress_callback:
                pct = int((idx / total_combinations) * 100)
                progress_callback(pct)
            
            # 백테스트 실행
            result = backtester.run(
                code, 
                start_date, 
                end_date, 
                strategy_params=params
            )
            
            # 평가 점수 계산 (수익률 - MDD/2)
            # 높은 수익률과 낮은 MDD를 선호
            score = result['profit_pct'] - (result['mdd'] / 2)
            
            result['params'] = params
            result['score'] = score
            self.all_results.append(result)
            
            # 최고 결과 업데이트
            if score > best_score:
                best_score = score
                self.best_params = params
                self.best_result = result
                logger.info(f"새로운 최고 점수: {score:.2f} (수익률: {result['profit_pct']:.2f}%, MDD: {result['mdd']:.2f}%)")
        
        if progress_callback:
            progress_callback(100)
        
        logger.info(f"최적화 완료. 최고 점수: {best_score:.2f}")
        logger.info(f"최적 파라미터: {self.best_params}")
        
        return self.best_result, self.best_params, self.all_results
    
    def get_top_results(self, n=5):
        """상위 N개 결과 반환"""
        sorted_results = sorted(self.all_results, key=lambda x: x['score'], reverse=True)
        return sorted_results[:n]
