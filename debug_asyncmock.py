import asyncio
from unittest.mock import AsyncMock, patch

async def main():
    print("Testing AsyncMock behavior...")
    
    # Scenario 1: Patch with AsyncMock
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        print(f"Mock object: {mock_sleep}")
        print(f"Is callable? {callable(mock_sleep)}")
        
        # This simulates await websockets.connect(...)
        try:
            await mock_sleep(0.1)
            print("Scenario 1: Success")
        except Exception as e:
            print(f"Scenario 1 Failed: {e}")

    # Scenario 2: Return value is AsyncMock
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        ret_val = AsyncMock()
        mock_sleep.return_value = ret_val
        
        try:
            result = await mock_sleep(0.1)
            print(f"Scenario 2 Result: {result}")
            # Now await the result? No, the code doesn't await the result of connect, it assigns it.
            # self.websocket = await websockets.connect(...)
            print("Scenario 2: Success")
        except Exception as e:
            print(f"Scenario 2 Failed: {e}")

    # Scenario 3: Awaiting the AsyncMock object directly
    m = AsyncMock()
    try:
        await m
        print("Scenario 3: Success")
    except Exception as e:
        print(f"Scenario 3 Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
