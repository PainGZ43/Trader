"""
AI Model Training Script
LSTM + XGBoost 모델 학습 스크립트
"""
import sys
from logger import logger
from ai.trainer import AITrainer

if __name__ == "__main__":
    # 기본값: 삼성전자, 1년, 1시간봉
    stock_code = sys.argv[1] if len(sys.argv) > 1 else '005930'
    period = sys.argv[2] if len(sys.argv) > 2 else '1y'
    interval = sys.argv[3] if len(sys.argv) > 3 else '1h'
    
    logger.info(f"Training with: stock={stock_code}, period={period}, interval={interval}")
    
    trainer = AITrainer()
    success = trainer.train_models(stock_code, period, interval)
    
    if success:
        logger.info("Training successful!")
        sys.exit(0)
    else:
        logger.error("Training failed!")
        sys.exit(1)
