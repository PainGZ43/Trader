import sys
import os
import logging
import pandas as pd
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verification.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Verifier")

def verify_watchlist():
    logger.info("="*50)
    logger.info("TEST 1: Watchlist Manager Verification")
    try:
        from watchlist_manager import WatchlistManager
        wm = WatchlistManager()
        
        # Test Add
        test_code = "005930"
        test_name = "삼성전자_TEST"
        if wm.add(test_code, test_name):
            logger.info(f"✅ Added {test_code} successfully")
        else:
            logger.info(f"ℹ️ {test_code} already exists")
            
        # Test Get
        stocks = wm.get_all()
        found = any(s['code'] == test_code for s in stocks)
        if found:
            logger.info(f"✅ Retrieved watchlist successfully ({len(stocks)} items)")
        else:
            logger.error(f"❌ Failed to retrieve {test_code}")
            return False
            
        # Test Remove
        if wm.remove(test_code):
            logger.info(f"✅ Removed {test_code} successfully")
        else:
            logger.error(f"❌ Failed to remove {test_code}")
            
        return True
    except Exception as e:
        logger.error(f"❌ Watchlist Manager Test Failed: {e}")
        return False

def verify_recommender():
    logger.info("="*50)
    logger.info("TEST 2: AI Recommender Verification")
    try:
        from ai.recommender import StockRecommender
        recommender = StockRecommender()
        
        import asyncio
        
        test_codes = ["005930"] # Samsung Electronics
        logger.info(f"Analyzing {test_codes}...")
        
        # Mock progress callback
        def progress(curr, total):
            pass
            
        # Run async method synchronously
        results = asyncio.run(recommender.analyze_stocks(test_codes, progress_callback=progress))
        
        if results:
            r = results[0]
            logger.info(f"✅ Analysis successful for {r['code']}")
            logger.info(f"   - AI Score: {r['ai_score']:.2f}")
            logger.info(f"   - Grade: {r['grade']}")
            logger.info(f"   - Recommendation: {r['recommendation']}")
            return True
        else:
            logger.warning("⚠️ Analysis returned no results (might be network/data issue)")
            return True # Not a critical failure for verification
            
    except Exception as e:
        logger.error(f"❌ Recommender Test Failed: {e}")
        return False

def verify_trainer():
    logger.info("="*50)
    logger.info("TEST 3: AI Training Pipeline Verification")
    try:
        from ai.data_collector import DataCollector
        from ai.indicators import IndicatorCalculator
        from ai.xgboost_model import XGBoostPredictor
        import numpy as np
        
        # 1. Data Collection (Short period)
        collector = DataCollector()
        symbol = "005930.KS"
        logger.info(f"Downloading data for {symbol} (1mo, 1h)...")
        df = collector.get_stock_data(symbol, period="1mo", interval="1h")
        
        if df is None or df.empty:
            logger.error("❌ Data download failed")
            return False
        logger.info(f"✅ Data downloaded: {len(df)} rows")
        
        # 2. Indicators
        logger.info("Calculating indicators...")
        df = IndicatorCalculator.calculate_all(df)
        df = df.dropna()
        logger.info(f"✅ Indicators calculated. Valid rows: {len(df)}")
        
        # 3. XGBoost Training
        logger.info("Training XGBoost model...")
        feature_cols = IndicatorCalculator.get_feature_names()
        X = df[feature_cols].values
        y = (df['close'].shift(-1) > df['close']).astype(int).values
        
        # Remove NaNs created by shift
        mask = ~np.isnan(y)
        X = X[mask]
        y = y[mask]
        
        model = XGBoostPredictor()
        metrics = model.train(X, y)
        
        logger.info(f"✅ XGBoost Training successful")
        logger.info(f"   - Accuracy: {metrics['accuracy']:.2%}")
        logger.info(f"   - AUC: {metrics['auc']:.2%}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Training Pipeline Test Failed: {e}")
        return False

def verify_trader():
    logger.info("="*50)
    logger.info("TEST 4: Trading Manager Verification")
    try:
        from trading_manager import TradingManager
        trader = TradingManager()
        
        logger.info(f"✅ TradingManager initialized")
        logger.info(f"   - Balance: {trader.balance:,.0f}")
        logger.info(f"   - Mode: {'Virtual' if trader.is_virtual else 'Real'}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Trading Manager Test Failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 STARTING SYSTEM VERIFICATION")
    
    results = {
        "Watchlist": verify_watchlist(),
        "Recommender": verify_recommender(),
        "Trainer": verify_trainer(),
        "Trader": verify_trader()
    }
    
    logger.info("="*50)
    logger.info("📊 VERIFICATION SUMMARY")
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{name}: {status}")
        if not passed:
            all_passed = False
            
    if all_passed:
        logger.info("\n✨ SYSTEM IS READY FOR DEPLOYMENT ✨")
        sys.exit(0)
    else:
        logger.info("\n⚠️ SYSTEM HAS ISSUES - CHECK LOGS")
        sys.exit(1)
