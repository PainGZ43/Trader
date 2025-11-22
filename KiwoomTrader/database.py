from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config
from datetime import datetime

Base = declarative_base()

class TradeLog(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    code = Column(String)
    name = Column(String)
    side = Column(String) # BUY / SELL
    price = Column(Float)
    qty = Column(Integer)
    strategy_score = Column(Float) # AI Score
    profit_pct = Column(Float, nullable=True)
    note = Column(Text, nullable=True)

class DailySummary(Base):
    __tablename__ = 'daily_summary'
    date = Column(String, primary_key=True)
    total_profit = Column(Float)
    trade_count = Column(Integer)
    win_rate = Column(Float)

engine = create_engine(Config.DB_PATH, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db():
    return Session()

def init_db():
    Base.metadata.create_all(engine)

