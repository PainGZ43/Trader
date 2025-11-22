"""
데이터베이스 관리 모듈
"""
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


class DatabaseManager:
    """SQLite 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str):
        """
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.initialize_database()
    
    def get_connection(self):
        """데이터베이스 연결 가져오기"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return self.conn
    
    def initialize_database(self):
        """데이터베이스 초기화 및 스키마 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 시장 데이터 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market VARCHAR(20) NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                value REAL NOT NULL,
                UNIQUE(market, timestamp)
            )
        ''')
        
        # 거래 이력 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market VARCHAR(20) NOT NULL,
                side VARCHAR(10) NOT NULL,
                order_type VARCHAR(20) NOT NULL,
                price REAL,
                volume REAL NOT NULL,
                executed_volume REAL,
                fee REAL,
                status VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                uuid VARCHAR(50) UNIQUE,
                strategy_name VARCHAR(50)
            )
        ''')
        
        # 포지션 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market VARCHAR(20) NOT NULL UNIQUE,
                entry_price REAL NOT NULL,
                current_price REAL,
                quantity REAL NOT NULL,
                profit_loss REAL,
                profit_loss_percent REAL,
                opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # AI 예측 결과 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market VARCHAR(20) NOT NULL,
                timestamp DATETIME NOT NULL,
                predicted_price REAL,
                confidence REAL,
                signal VARCHAR(10),
                model_version VARCHAR(20),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 전략 성과 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name VARCHAR(50) NOT NULL,
                market VARCHAR(20),
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0,
                win_rate REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                start_date DATE,
                end_date DATE,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 설정 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key VARCHAR(50) PRIMARY KEY,
                value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 로그 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level VARCHAR(10),
                message TEXT,
                module VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_market ON market_data(market)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_market_timestamp ON predictions(market, timestamp)')
        
        conn.commit()
        print(f"✅ 데이터베이스 초기화 완료: {self.db_path}")
    
    # === 시장 데이터 관련 ===
    
    def insert_market_data(self, market: str, timestamp: datetime, ohlcv: Dict[str, float]):
        """시장 데이터 삽입"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO market_data 
                (market, timestamp, open, high, low, close, volume, value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (market, timestamp, ohlcv['open'], ohlcv['high'], ohlcv['low'],
                  ohlcv['close'], ohlcv['volume'], ohlcv.get('value', 0)))
            conn.commit()
        except Exception as e:
            print(f"시장 데이터 삽입 에러: {e}")
            conn.rollback()
    
    def get_market_data(self, market: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """시장 데이터 조회"""
        conn = self.get_connection()
        
        query = '''
            SELECT * FROM market_data
            WHERE market = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        '''
        
        df = pd.read_sql_query(query, conn, params=(market, start_date, end_date))
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    # === 거래 관련 ===
    
    def insert_trade(self, trade_info: Dict[str, Any]):
        """거래 이력 저장"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO trades 
                (market, side, order_type, price, volume, executed_volume, 
                 fee, status, uuid, strategy_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_info.get('market'),
                trade_info.get('side'),
                trade_info.get('order_type'),
                trade_info.get('price'),
                trade_info.get('volume'),
                trade_info.get('executed_volume'),
                trade_info.get('fee'),
                trade_info.get('status'),
                trade_info.get('uuid'),
                trade_info.get('strategy_name')
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"거래 이력 저장 에러: {e}")
            conn.rollback()
            return None
    
    def get_trades(self, market: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """거래 이력 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if market:
            cursor.execute('''
                SELECT * FROM trades 
                WHERE market = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (market, limit))
        else:
            cursor.execute('''
                SELECT * FROM trades 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # === 포지션 관련 ===
    
    def insert_position(self, market: str, entry_price: float, quantity: float):
        """포지션 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO positions (market, entry_price, current_price, quantity)
                VALUES (?, ?, ?, ?)
            ''', (market, entry_price, entry_price, quantity))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"포지션 생성 에러: {e}")
            conn.rollback()
            return None
    
    def update_position(self, market: str, current_price: float):
        """포지션 업데이트"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE positions
            SET current_price = ?,
                profit_loss = (? - entry_price) * quantity,
                profit_loss_percent = ((? - entry_price) / entry_price) * 100,
                updated_at = CURRENT_TIMESTAMP
            WHERE market = ?
        ''', (current_price, current_price, current_price, market))
        conn.commit()
    
    def get_open_positions(self) -> List[Dict]:
        """열린 포지션 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM positions')
        return [dict(row) for row in cursor.fetchall()]
    
    def close_position(self, market: str):
        """포지션 종료"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM positions WHERE market = ?', (market,))
        conn.commit()
    
    # === AI 예측 관련 ===
    
    def insert_prediction(self, market: str, predicted_price: float, 
                         confidence: float, signal: str, model_version: str):
        """AI 예측 저장"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions 
            (market, timestamp, predicted_price, confidence, signal, model_version)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
        ''', (market, predicted_price, confidence, signal, model_version))
        conn.commit()
    
    # === 기타 ===
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """커스텀 쿼리 실행"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __del__(self):
        """소멸자"""
        self.close()


if __name__ == "__main__":
    # 테스트
    db = DatabaseManager("./database/test_trading.db")
    print("✅ 데이터베이스 초기화 완료")
    
    # 테스트 데이터 삽입
    db.insert_market_data(
        "KRW-BTC",
        datetime.now(),
        {'open': 50000000, 'high': 51000000, 'low': 49000000, 
         'close': 50500000, 'volume': 100, 'value': 5000000000}
    )
    print("✅ 시장 데이터 삽입 완료")
    
    # 포지션 테스트
    db.insert_position("KRW-BTC", 50000000, 0.1)
    print("✅ 포지션 생성 완료")
    
    positions = db.get_open_positions()
    print(f"✅ 열린 포지션: {len(positions)}개")
    
    db.close()
