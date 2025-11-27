import pytest
import asyncio
from execution.account_manager import AccountManager
from execution.paper_exchange import PaperExchange

@pytest.mark.asyncio
async def test_account_manager_sync(tmp_path):
    # Setup Paper Exchange with 10M
    exchange = PaperExchange(initial_capital=10_000_000)
    
    # Init Manager
    manager = AccountManager(exchange)
    
    # 1. Test Initial Sync
    await manager.update_balance()
    assert manager.balance["deposit"] == 10_000_000
    assert manager.balance["total_asset"] == 10_000_000
    
    # 2. Test Buying Power (Normal)
    # Need 1M, Have 10M -> OK
    assert manager.check_buying_power(1_000_000) is True
    
    # 3. Test Buying Power (Low Cash)
    # Simulate buying 9.5M worth of stock (Cash -> 0.5M)
    # PaperExchange doesn't allow manual balance set easily, so we mock it or trade.
    # Let's trade.
    # Buy 95 shares @ 100,000 = 9,500,000
    # Fee ~ 0.015% -> Small.
    
    # Send Order directly to Exchange
    await exchange.send_order("005930", 1, 95, 100000, "00")
    quote = {"symbol": "005930", "current_price": 100000, "ask1": 100000, "bid1": 99000}
    exchange.match_orders(quote)
    
    # Sync
    await manager.update_balance()
    
    # Cash should be < 500,000 (due to fees)
    # Total Asset ~ 10,000,000
    # Ratio < 0.05 (5%)
    # Min Ratio is 0.1 (10%)
    
    assert manager.balance["deposit"] < 1_000_000
    assert manager.check_buying_power(100_000) is False # Blocked due to low cash ratio
    
    # 4. Test Summary
    summary = manager.get_summary()
    assert "005930" in summary["positions"]
    assert summary["positions"]["005930"]["qty"] == 95
