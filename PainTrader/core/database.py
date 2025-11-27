import aiosqlite
import os
from core.config import config
from core.logger import get_logger

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = get_logger("Database")
        self.db_path = config.get("DB_PATH", "trade.db")
        self.conn = None

    async def connect(self):
        if self.conn is None:
            try:
                self.conn = await aiosqlite.connect(self.db_path)
                self.conn.row_factory = aiosqlite.Row
                
                # Enable WAL mode for better concurrency
                await self.conn.execute("PRAGMA busy_timeout=30000;") # 30 seconds
                await self.conn.execute("PRAGMA journal_mode=WAL;")
                await self.conn.execute("PRAGMA synchronous=NORMAL;") # Recommended for WAL
                
                self.logger.info(f"Connected to database: {self.db_path} (WAL Mode)")
                await self._create_tables()
            except Exception as e:
                self.logger.critical(f"Failed to connect to database: {e}")
                raise

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None
            self.logger.info("Database connection closed")

    async def _create_tables(self):
        try:
            # Market Data Table
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    timestamp DATETIME,
                    symbol TEXT,
                    interval TEXT,
                    open INTEGER,
                    high INTEGER,
                    low INTEGER,
                    close INTEGER,
                    volume INTEGER,
                    PRIMARY KEY (timestamp, symbol, interval)
                )
            """)

            # Trade History Table
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    side TEXT,
                    price INTEGER,
                    quantity INTEGER,
                    strategy TEXT,
                    profit INTEGER,
                    profit_rate REAL
                )
            """)

            # Strategy State Persistence Table
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_state (
                    strategy_id TEXT PRIMARY KEY,
                    symbol TEXT,
                    current_position INTEGER,
                    avg_entry_price REAL,
                    accumulated_profit REAL,
                    indicators TEXT,
                    last_update DATETIME
                )
            """)

            # Market Code Master Table
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS market_code (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    market TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Paper Trading Account Table
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS paper_account (
                    account_id TEXT PRIMARY KEY,
                    deposit REAL,
                    positions_json TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await self.conn.commit()
            self.logger.info("Database tables initialized")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise

    async def execute(self, query, params=()):
        if not self.conn:
            await self.connect()
        try:
            async with self.conn.execute(query, params) as cursor:
                await self.conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Query execution failed: {query} | {e}")
            raise

    async def fetch_all(self, query, params=()):
        if not self.conn:
            await self.connect()
        try:
            async with self.conn.execute(query, params) as cursor:
                return await cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Query fetch failed: {query} | {e}")
            raise

    async def cleanup_old_data(self, tick_retention_days=7, candle_retention_days=30):
        """
        Delete old market data based on retention policy.
        """
        if not self.conn:
            await self.connect()
            
        try:
            self.logger.info("Starting Database Cleanup...")
            
            # 1. Cleanup Ticks
            query_tick = f"DELETE FROM market_data WHERE interval='tick' AND timestamp < date('now', '-{tick_retention_days} days')"
            async with self.conn.execute(query_tick) as cursor:
                self.logger.info(f"Deleted {cursor.rowcount} old tick records.")
                
            # 2. Cleanup 1m Candles
            query_candle = f"DELETE FROM market_data WHERE interval='1m' AND timestamp < date('now', '-{candle_retention_days} days')"
            async with self.conn.execute(query_candle) as cursor:
                self.logger.info(f"Deleted {cursor.rowcount} old candle records.")
                
            await self.conn.commit()
            self.logger.info("Database Cleanup Completed.")
            
        except Exception as e:
            self.logger.error(f"Database Cleanup Failed: {e}")

db = Database()
