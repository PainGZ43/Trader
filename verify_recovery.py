import asyncio
import logging
from data.websocket_client import WebSocketClient
from data.rate_limiter import RateLimiter
from core.logger import get_logger

logger = get_logger("VerifyRecovery")

async def test_websocket_reconnection():
    print("\n[TEST] WebSocket Reconnection Logic")
    
    # We need to patch websockets.connect inside the module
    import data.websocket_client as wc
    import websockets
    
    original_connect = websockets.connect
    fail_count = 0
    
    class MockWebSocket:
        async def recv(self):
            await asyncio.sleep(100) # Hang
        async def close(self):
            pass
    
    async def mock_connect(*args, **kwargs):
        nonlocal fail_count
        if fail_count < 2:
            fail_count += 1
            print(f"  -> Simulating Connection Failure ({fail_count}/2)")
            raise Exception("Simulated Network Error")
        print("  -> Simulating Connection Success")
        return MockWebSocket()

    # Apply patch
    wc.websockets.connect = mock_connect
    
    ws_client = wc.WebSocketClient()
    ws_client.mock_mode = False # Force real mode logic to trigger connect
    
    # Start client (it should retry)
    task = asyncio.create_task(ws_client.connect())
    
    await asyncio.sleep(6) # Wait for retries
    
    if fail_count == 2:
        print("[PASS] WebSocket retried and connected.")
    else:
        print(f"[FAIL] WebSocket did not retry enough. Fail count: {fail_count}")
        
    ws_client.running = False
    ws_client._stop_event.set()
    task.cancel()
    
    # Restore patch
    wc.websockets.connect = original_connect

async def test_rate_limiter():
    print("\n[TEST] Rate Limiter Logic")
    # 5 tokens per second
    limiter = RateLimiter(max_tokens=5, refill_rate=5)
    
    start_time = asyncio.get_event_loop().time()
    
    # Consume 10 tokens (should take ~1 second)
    for i in range(10):
        await limiter.acquire()
        # print(f"  -> Token {i+1} acquired")
        
    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    
    print(f"  -> Consumed 10 tokens in {duration:.2f} seconds")
    
    if duration >= 0.8: # Should be at least close to 1s
        print("[PASS] Rate Limiter throttled requests.")
    else:
        print(f"[FAIL] Rate Limiter too fast: {duration:.2f}s")

async def main():
    await test_websocket_reconnection()
    await test_rate_limiter()

if __name__ == "__main__":
    asyncio.run(main())
