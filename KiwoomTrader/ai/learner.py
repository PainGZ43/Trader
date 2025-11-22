from logger import logger
from ai.trainer import AITrainer

class AILearner:
    """
    AI 학습 관리 클래스
    주기적인 재학습을 담당
    """
    def __init__(self):
        self.trainer = AITrainer()
        
    def retrain(self):
        """
        모델 재학습 실행
        """
        logger.info("Starting Nightly Retraining...")
        
        try:
            # 대표 종목(삼성전자)으로 모델 재학습
            # 최근 2년치 데이터 사용
            success = self.trainer.train_models(stock_code='005930', period='2y', interval='1h')
            
            if success:
                logger.info("Retraining Completed Successfully.")
            else:
                logger.error("Retraining Failed.")
                
        except Exception as e:
            logger.error(f"Error during retraining: {e}")
