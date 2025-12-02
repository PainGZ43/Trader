import aiohttp
import asyncio

async def test_scraping():
    print("Testing Naver Finance Scraping...")
    
    # 1. KOSPI
    url_kospi = "https://finance.naver.com/sise/sise_index.naver?code=KOSPI"
    await fetch_and_parse("KOSPI", url_kospi)

    # 2. KOSDAQ
    url_kosdaq = "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ"
    await fetch_and_parse("KOSDAQ", url_kosdaq)

async def fetch_and_parse(name, url):
    print(f"\n--- Fetching {name} ---")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # 1. Price
                    price = 0.0
                    if 'id="now_value"' in text:
                        start_idx = text.find('id="now_value"')
                        val_start = text.find('>', start_idx) + 1
                        val_end = text.find('<', val_start)
                        val_str = text[val_start:val_end].replace(",", "")
                        price = float(val_str)
                        print(f"Price: {price}")
                    else:
                        print("Failed to find 'now_value'")

                    # 2. Change
                    if 'id="change_value_and_rate"' in text:
                        c_start = text.find('id="change_value_and_rate"')
                        
                        # Find inner span for Amount
                        amt_start_tag = text.find('<span>', c_start)
                        if amt_start_tag != -1:
                            amt_start = amt_start_tag + 6 # len('<span>')
                            amt_end = text.find('</span>', amt_start)
                            change_amt = text[amt_start:amt_end].strip()
                            
                            # Find Percent (Text after </span>)
                            pct_start = amt_end + 7 # len('</span>')
                            pct_end = text.find('<', pct_start)
                            change_pct = text[pct_start:pct_end].strip().replace("%", "")
                            
                            # Determine sign from class (point_dn/up)
                            # Look at the parent element class usually
                            # <div class="change_value_and_rate point_dn"> ... </div>
                            # But here we are inside a span with id.
                            # Let's check the text itself for signs?
                            # Usually Naver puts sign in text? "+1.90%" yes.
                            
                            if "+" in change_pct:
                                sign = "+"
                            elif "-" in change_pct:
                                sign = "-"
                            else:
                                # Fallback to class check
                                if "point_dn" in text[c_start-100:c_start+100]:
                                    sign = "-"
                                elif "point_up" in text[c_start-100:c_start+100]:
                                    sign = "+"
                                else:
                                    sign = ""
                            
                            # Clean up amount (remove existing signs if any)
                            change_amt = change_amt.replace("+", "").replace("-", "")
                            change_pct = change_pct.replace("+", "").replace("-", "")
                            
                            print(f"Change: {sign}{change_amt} ({sign}{change_pct}%)")
                        else:
                            print("Failed to find inner span for amount")
                    else:
                        print("Failed to find 'change_value_and_rate'")
                        
                else:
                    print(f"HTTP Error: {response.status}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraping())
