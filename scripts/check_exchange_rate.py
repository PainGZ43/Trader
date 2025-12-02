import asyncio
import aiohttp
import sys

async def check_rate():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    print(f"Fetching from: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rate = data.get("rates", {}).get("KRW")
                    print(f"Current USD/KRW Rate: {rate}")
                else:
                    print(f"Failed to fetch. Status: {response.status}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_rate())
