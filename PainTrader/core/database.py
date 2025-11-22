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
                self.logger.info(f"Connected to database: {self.db_path}")
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
                    symbol TEXT PRIMARY KEY,
                    state_json TEXT,
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

db = Database()
