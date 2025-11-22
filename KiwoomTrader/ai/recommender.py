"""
Stock Recommender
AI 기반 종목 추천 시스템
"""
import asyncio
from logger import logger
from ai.predictor import AIPredictor
from ai.sentiment import SentimentAnalyzer
from ai.indicators import IndicatorCalculator
from ai.data_collector import DataCollector
import pandas as pd

class StockRecommender:
    """AI 기반 종목 추천기"""
    
    def __init__(self):
        self.predictor = AIPredictor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.data_collector = DataCollector()
    
    async def analyze_stock(self, stock_code):
        """
        단일 종목 분석
        
        Returns:
            dict with score, signals, and recommendation
        """
        try:
            logger.info(f"Analyzing {stock_code}...")
            
            # 1. 최근 데이터 가져오기
            yf_symbol = DataCollector.convert_korean_code(stock_code)
            df = self.data_collector.get_stock_data(yf_symbol, period='1mo', interval='1h', use_cache=True)
            
            if df is None or len(df) < 100:
                return None
            
            # 2. 기술적 지표 계산
            df = IndicatorCalculator.calculate_all(df)
            df = df.dropna()
            
            if len(df) < 50:
                return None
            
            # 3. AI 예측 (최근 데이터로)
            latest_data = {
                'open': df['open'].iloc[-1],
                'high': df['high'].iloc[-1],
                'low': df['low'].iloc[-1],
                'close': df['close'].iloc[-1],
                'volume': df['volume'].iloc[-1],
                'change': df['close'].iloc[-1] - df['close'].iloc[-2]
            }
            
            # 데이터 업데이트
            for i in range(min(100, len(df))):
                self.predictor.update_data({
                    'open': df['open'].iloc[-(100-i)],
                    'high': df['high'].iloc[-(100-i)],
                    'low': df['low'].iloc[-(100-i)],
                    'close': df['close'].iloc[-(100-i)],
                    'volume': df['volume'].iloc[-(100-i)],
                    'change': 0
                })
            
            ai_score = self.predictor.predict(latest_data)
            
            # 4. 감성 분석
            sentiment_score = await self.sentiment_analyzer.get_sentiment_score(stock_code)
            
            # 5. 기술적 신호
            current = df.iloc[-1]
            signals = {
                'rsi': current['RSI'],
                'rsi_signal': 'oversold' if current['RSI'] < 30 else ('overbought' if current['RSI'] > 70 else 'neutral'),
                'macd_signal': 'bullish' if current['MACD'] > current['MACD_Signal'] else 'bearish',
                'bb_position': current['BB_Position'],
                'volume_ratio': current['Volume_Ratio'],
                'trend': 'uptrend' if current['close'] > current['SMA_20'] else 'downtrend'
            }
            
            # 6. 종합 점수 계산
            # AI (40%) + Sentiment (30%) + Technical (30%)
            technical_score = 0.5  # 기본값
            
            # RSI oversold → 매수 기회
            if current['RSI'] < 35:
                technical_score += 0.3
            elif current['RSI'] < 50:
                technical_score += 0.1
            elif current['RSI'] > 65:
                technical_score -= 0.2
            
            # MACD bullish
            if current['MACD'] > current['MACD_Signal']:
                technical_score += 0.2
            
            # Volume 증가
            if current['Volume_Ratio'] > 1.5:
                technical_score += 0.1
            
            technical_score = max(0, min(1, technical_score))
            
            # 정규화된 감성 점수 (−1~1 → 0~1)
            normalized_sentiment = (sentiment_score + 1) / 2
            
            # 최종 점수
            final_score = (
                ai_score * 0.4 +
                normalized_sentiment * 0.3 +
                technical_score * 0.3
            )
            
            # 7. 추천 등급
            if final_score >= 0.75:
                recommendation = '강력 매수'
                grade = 'A'
            elif final_score >= 0.65:
                recommendation = '매수'
                grade = 'B'
            elif final_score >= 0.55:
                recommendation = '관망'
                grade = 'C'
            elif final_score >= 0.45:
                recommendation = '중립'
                grade = 'D'
            else:
                recommendation = '매도 고려'
                grade = 'F'
            
            result = {
                'code': stock_code,
                'score': final_score,
                'ai_score': ai_score,
                'sentiment_score': sentiment_score,
                'technical_score': technical_score,
                'signals': signals,
                'recommendation': recommendation,
                'grade': grade,
                'current_price': current['close']
            }
            
            logger.info(f"{stock_code}: {recommendation} (Score: {final_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {stock_code}: {e}")
            return None
    
    async def get_recommendations(self, stock_list, top_n=5):
        """
        여러 종목 분석 후 상위 N개 추천
        
        Args:
            stock_list: 종목 코드 리스트
            top_n: 추천할 종목 수
        
        Returns:
            list of recommendations sorted by score
        """
        logger.info(f"Analyzing {len(stock_list)} stocks...")
        
        tasks = [self.analyze_stock(code) for code in stock_list]
        results = await asyncio.gather(*tasks)
        
        # None 제거 및 점수순 정렬
        valid_results = [r for r in results if r is not None]
        sorted_results = sorted(valid_results, key=lambda x: x['score'], reverse=True)
        
        return sorted_results[:top_n]

    async def analyze_stocks(self, stock_list, progress_callback=None):
        """UI 호환성을 위한 별칭 메서드"""
        # progress_callback은 여기서 직접 처리하기 어려우므로 무시하거나 
        # get_recommendations 내부 로직을 수정해야 함.
        # 일단 단순 래퍼로 구현
        return await self.get_recommendations(stock_list, top_n=len(stock_list))
