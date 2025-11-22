"""
Strategy Manager
전략 저장 및 관리
"""
import json
import os
from datetime import datetime
from logger import logger

class StrategyManager:
    """전략 관리 클래스"""
    
    def __init__(self, filepath='data/strategies.json'):
        self.filepath = filepath
        self.strategies = []
        self.active_strategy = None
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.load()
    
    def save_optimization_results(self, stock_code, results, best_params):
        """
        최적화 결과 저장
        
        Args:
            stock_code: 종목 코드
            results: 모든 최적화 결과 리스트
            best_params: 최고 성능 파라미터
        """
        # 상위 10개만 저장
        top_10 = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
        
        strategy_data = {
            'timestamp': datetime.now().isoformat(),
            'stock_code': stock_code,
            'best_params': best_params,
            'top_10': top_10,
            'total_tested': len(results)
        }
        
        self.strategies.append(strategy_data)
        
        # 최근 20개만 유지
        if len(self.strategies) > 20:
            self.strategies = self.strategies[-20:]
        
        self._save_to_file()
        logger.info(f"Saved optimization results for {stock_code}, {len(top_10)} strategies")
    
    def _save_to_file(self):
        """파일에 저장"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'strategies': self.strategies,
                    'active_strategy': self.active_strategy
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving strategies: {e}")
    
    def load(self):
        """저장된 전략 로드"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.strategies = data.get('strategies', [])
                    self.active_strategy = data.get('active_strategy')
                logger.info(f"Loaded {len(self.strategies)} optimization results")
            except Exception as e:
                logger.error(f"Error loading strategies: {e}")
                self.strategies = []
                self.active_strategy = None
    
    def get_latest_results(self):
        """최근 최적화 결과 반환"""
        if not self.strategies:
            return None
        return self.strategies[-1]
    
    def get_all_results(self):
        """모든 최적화 결과 반환"""
        return self.strategies.copy()
    
    def set_active_strategy(self, params):
        """활성 전략 설정"""
        self.active_strategy = params
        self._save_to_file()
        logger.info(f"Active strategy set: {params}")
    
    def get_active_strategy(self):
        """현재 활성 전략 반환"""
        return self.active_strategy
    
    def clear_active_strategy(self):
        """활성 전략 해제"""
        self.active_strategy = None
        self._save_to_file()
        logger.info("Active strategy cleared")
