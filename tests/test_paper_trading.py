import pytest
import asyncio
from execution.paper_exchange import PaperExchange
from execution.engine import ExecutionEngine
from strategy.base_strategy import Signal
from datetime import datetime

from datetime import datetime
from core.database import Database

@pytest.mark.asyncio
async def test_paper_exchange_flow(tmp_path):
    # Setup Temp DB
    db_path = tmp_path / "test_paper.db"
    db = Database()
    db.db_path = str(db_path)
    if db.conn:
        await db.close()
    await db.connect()
    
    # 1. Initialize
    exchange = PaperExchange(initial_capital=10_000_000)
    assert exchange.balance['deposit'] == 10_000_000
    
    # 2. Send Buy Order (Limit 60,000)
    # Current Price 59,000 (Ask 59,100) -> Should NOT match if Limit < Ask?
    # Wait, Limit Buy matches if Price <= Limit.
    # If Limit is 60,000 and Ask is 59,100, it matches at 59,100 (Better Price).
    
    res = await exchange.send_order("005930", 1, 10, 60000, "00")
    assert res['result_code'] == 0
    order_id = res['order_no']
    assert order_id in exchange.active_orders
    
    # 3. Match Order
    # Quote: Ask 59000. Limit 60000 >= Ask 59000 -> Match!
    quote = {"symbol": "005930", "current_price": 59000, "ask1": 59000, "bid1": 58900}
    exchange.match_orders(quote)
    
    assert order_id not in exchange.active_orders
    assert "005930" in exchange.positions
    pos = exchange.positions["005930"]
    assert pos['qty'] == 10
    assert pos['avg_price'] == 59000 # Matched at Ask
    
    # Check Balance (10 * 59000 = 590,000 + Fee)
    fee = 590000 * 0.00015
    expected_deposit = 10_000_000 - 590000 - fee
    assert exchange.balance['deposit'] == expected_deposit
    
    # 4. Send Sell Order (Market)
    res = await exchange.send_order("005930", 2, 5, 0, "03")
    order_id_sell = res['order_no']
    
    # Match (Market sells at Bid)
    quote['bid1'] = 60000 # Price went up
    exchange.match_orders(quote)
    
    assert exchange.positions["005930"]['qty'] == 5
    
    # 5. Test Persistence
    await exchange.save_state()
    
    # New Instance
    new_exchange = PaperExchange(initial_capital=100) # Dummy capital
    await new_exchange.load_state()
    
    # Should match previous state
    assert new_exchange.balance['deposit'] == exchange.balance['deposit']
    assert new_exchange.positions["005930"]['qty'] == 5
    
    # 6. Test Liquidity Check
    # Ask Size = 1. Order Qty = 10. Should NOT fill.
    res = await exchange.send_order("005930", 1, 10, 60000, "00")
    order_id_liq = res['order_no']
    
    quote_low_liq = {"symbol": "005930", "current_price": 60000, "ask1": 60000, "bid1": 59000, "ask_size1": 1}
    exchange.match_orders(quote_low_liq)
    
    assert order_id_liq in exchange.active_orders # Still Pending
    
    # Cancel the large order to prevent it from filling in next step
    await exchange.cancel_order(order_id_liq, "005930", 10)
    
    # 7. Test Slippage (Market Order)
    res = await exchange.send_order("005930", 1, 1, 0, "03") # Market Buy
    
    # Quote with enough liquidity
    quote_slippage = {"symbol": "005930", "current_price": 60000, "ask1": 60000, "bid1": 59000, "ask_size1": 100}
    exchange.match_orders(quote_slippage)
    
    # Check logs or position price for slippage
    # Since we can't easily check exact price due to randomness, we assume it executed.
    # The position qty should increase by 1 (Total 6)
    assert exchange.positions["005930"]['qty'] == 6
    
@pytest.mark.asyncio
async def test_execution_engine_paper_mode():
    # Mock Kiwoom (not used in Paper mode but required for init)
    from data.kiwoom_rest_client import KiwoomRestClient
    kiwoom = KiwoomRestClient()
    
    engine = ExecutionEngine(kiwoom, mode="PAPER")
    await engine.initialize()
    
    assert isinstance(engine.exchange, PaperExchange)
    assert engine.exchange.initial_capital == 100_000_000 # Default
    
    # Execute Signal
    signal = Signal("005930", "BUY", 60000, datetime.now(), "Test")
    await engine.execute_signal(signal, 10)
    
    # Check Order Sent to Paper Exchange
    assert len(engine.exchange.active_orders) == 1
