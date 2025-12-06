import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.kiwoom_rest_client import KiwoomRestClient
from execution.account_manager import AccountManager
from core.event_bus import event_bus

async def verify_account_loading():
    print("=== Verifying Account Loading ===")
    
    # 1. Initialize Client
    kiwoom = KiwoomRestClient()
    
    # 2. Initialize AccountManager
    # We use KiwoomRestClient directly as the exchange
    account_manager = AccountManager(kiwoom)
    
    # 3. Subscribe to Events
    def on_account_summary(event):
        print(f"\n[EVENT] Account Summary Received:")
        print(f"  - Total Asset: {event.data['balance'].get('total_asset', 0):,.0f}")
        print(f"  - Deposit: {event.data['balance'].get('deposit', 0):,.0f}")
        print(f"  - Total PnL: {event.data['balance'].get('total_pnl', 0):,.0f}")
        
    def on_portfolio(event):
        print(f"\n[EVENT] Portfolio Received ({len(event.data)} items):")
        for item in event.data:
            print(f"  - {item['name']} ({item['code']}): {item['qty']} qty, {item['earning_rate']}%")

    event_bus.subscribe("account.summary", on_account_summary)
    event_bus.subscribe("account.portfolio", on_portfolio)
    
    # 4. Update Balance (Manual Trigger)
    print("Requesting Account Balance...")
    await account_manager.update_balance()
    
    # 5. Check Internal State
    print("\n[Internal State]")
    summary = account_manager.get_summary()
    print(f"Balance: {summary['balance']}")
    print(f"Positions: {len(summary['positions'])}")
    
    # Wait a bit for events to process
    await asyncio.sleep(1)
    
    await kiwoom.close()
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    asyncio.run(verify_account_loading())
