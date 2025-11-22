"""
Upbit API 래퍼 - 실시간 데이터 수집
"""
import pyupbit
import pandas as pd
from datetime import datetime
import time
from PyQt5.QtCore import QThread, pyqtSignal


class UpbitAPI:
    """Upbit API 래퍼 클래스"""
    
    def __init__(self):
        self.tickers_cache = None
        self.last_update = None
        
        # OHLCV 데이터 캐싱
        self.ohlcv_cache = {}  # {(ticker, interval): (df, timestamp)}
        self.cache_ttl = {  # 간격별 캐시 유효 시간 (초)
            'minute1': 30,
            'minute3': 60,
            'minute5': 120,
            'minute10': 300,
            'minute15': 300,
            'minute30': 600,
            'minute60': 1200,
            'day': 3600,
            'week': 7200,
            'month': 14400,
        }
        
    def get_all_tickers(self, fiat="KRW"):
        """모든 마켓 티커 조회"""
        try:
            tickers = pyupbit.get_tickers(fiat=fiat)
            return tickers
        except Exception as e:
            print(f"티커 조회 실패: {e}")
            return []
    
    def get_current_price(self, ticker):
        """현재가 조회"""
        try:
            price = pyupbit.get_current_price(ticker)
            # 0이나 None은 유효하지 않은 값
            if price is None or price == 0:
                return None
            return price
        except Exception as e:
            # 에러 로그를 너무 자주 출력하지 않도록 필터링
            if "0" not in str(e):  # 0 에러는 로그 스킵
                print(f"현재가 조회 실패 ({ticker}): {e}")
            return None
    
    def get_ohlcv(self, ticker, interval="minute1", count=200, use_cache=False):
        """OHLCV 데이터 조회
        
        Args:
            ticker: 마켓 코드 (예: KRW-BTC)
            interval: 시간 간격
                - minute1, minute3, minute5, minute10, minute15, minute30, minute60, minute240
                - day, week, month
            count: 캔들 개수 (최대 200)
            use_cache: 캐싱 사용 여부
        """
        # 캐싱 사용 시 캐시 확인
        if use_cache:
            cache_key = (ticker, interval)
            if cache_key in self.ohlcv_cache:
                cached_df, cached_time = self.ohlcv_cache[cache_key]
                age = time.time() - cached_time
                ttl = self.cache_ttl.get(interval, 300)
                
                if age < ttl:
                    return cached_df
        
        # 캐시 없거나 만료 시 API 호출
        try:
            df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
            if df is not None and not df.empty:
                # 캐싱
                if use_cache:
                    cache_key = (ticker, interval)
                    self.ohlcv_cache[cache_key] = (df, time.time())
                return df
            return None
        except Exception as e:
            print(f"OHLCV 조회 실패 ({ticker}): {e}")
            return None
    
    def get_market_info(self, ticker):
        """마켓 상세 정보 조회"""
        try:
            # 현재가
            current_price = self.get_current_price(ticker)
            
            # 일봉 데이터로 24시간 변동률 계산
            df = self.get_ohlcv(ticker, interval="day", count=2)
            
            if df is not None and len(df) >= 2:
                prev_close = df.iloc[-2]['close']
                current = df.iloc[-1]['close']
                change = ((current - prev_close) / prev_close) * 100
                
                return {
                    'ticker': ticker,
                    'current_price': current_price,
                    'change_percent': change,
                    'high_24h': df.iloc[-1]['high'],
                    'low_24h': df.iloc[-1]['low'],
                    'volume_24h': df.iloc[-1]['volume'],
                }
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'change_percent': 0,
            }
            
        except Exception as e:
            print(f"마켓 정보 조회 실패 ({ticker}): {e}")
            return None
    
    def get_orderbook(self, ticker):
        """호가 정보 조회"""
        try:
            orderbook = pyupbit.get_orderbook(ticker)
            if orderbook and len(orderbook) > 0:
                return orderbook[0]
            return None
        except Exception as e:
            print(f"호가 조회 실패 ({ticker}): {e}")
            return None
    
    def clear_cache(self):
        """캐시 초기화"""
        self.ohlcv_cache = {}
        print("캐시 초기화 완료")
    
    def get_cache_stats(self):
        """캐시 통계"""
        return {
            'cached_items': len(self.ohlcv_cache),
            'cached_tickers': list(set([k[0] for k in self.ohlcv_cache.keys()]))
        }


class MarketDataUpdater(QThread):
    """실시간 마켓 데이터 업데이트 스레드"""
    
    # 시그널 정의
    data_updated = pyqtSignal(list)  # 마켓 데이터 업데이트
    
    def __init__(self, fiat="KRW", update_interval=5):
        super().__init__()
        self.api = UpbitAPI()
        self.fiat = fiat
        self.update_interval = update_interval
        self.running = True
        
    def run(self):
        """스레드 실행"""
        while self.running:
            try:
                # 모든 티커 조회
                tickers = self.api.get_all_tickers(self.fiat)
                
                if tickers:
                    market_data = []
                    
                    # 각 티커별 정보 수집 (처음 20개만)
                    for ticker in tickers[:20]:
                        info = self.api.get_market_info(ticker)
                        if info:
                            market_data.append(info)
                    
                    # 시그널 발생
                    self.data_updated.emit(market_data)
                
                # 대기
                self.msleep(self.update_interval * 1000)
                
            except Exception as e:
                print(f"데이터 업데이트 에러: {e}")
                self.msleep(5000)
    
    def stop(self):
        """스레드 중지"""
        self.running = False
