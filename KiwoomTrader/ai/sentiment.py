import aiohttp
import asyncio
from bs4 import BeautifulSoup
from logger import logger
import re
import json

class SentimentAnalyzer:
    def __init__(self):
        # Domestic (Korean) Keywords
        self.positive_keywords_kr = [
            "상승", "급등", "호재", "수주", "계약", "최대", "성장", "이익", "흑자", 
            "돌파", "개선", "확대", "성공", "기대", "매수", "강세", "최고", "유망",
            "협력", "제휴", "승인", "개발", "공급"
        ]
        self.negative_keywords_kr = [
            "하락", "급락", "악재", "손실", "적자", "우려", "둔화", "감소", 
            "실패", "불확실", "매도", "약세", "최저", "제재", "중단", "해지",
            "소송", "규제", "위기", "쇼크"
        ]

        # Global (English) Keywords
        self.positive_keywords_en = [
            "surge", "jump", "gain", "profit", "growth", "record", "deal", "contract",
            "beat", "bull", "bullish", "buy", "upgrade", "success", "partnership",
            "approve", "launch", "breakthrough", "outperform", "rally"
        ]
        self.negative_keywords_en = [
            "drop", "fall", "plunge", "loss", "miss", "bear", "bearish", "sell",
            "downgrade", "fail", "concern", "worry", "risk", "crash", "slump",
            "lawsuit", "ban", "sanction", "halt", "debt"
        ]

    async def fetch_news_titles_kr(self, code: str, limit: int = 10) -> list:
        """
        Fetches recent news titles for a given stock code from Naver Finance.
        """
        url = f"https://finance.naver.com/item/news_news.nhn?code={code}"
        titles = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        links = soup.select('.title a')
                        
                        for link in links[:limit]:
                            title = link.get_text(strip=True)
                            if title:
                                titles.append(title)
                    else:
                        logger.warning(f"Failed to fetch KR news for {code}: Status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching KR news for {code}: {e}")
            
        return titles

    async def fetch_reddit_posts(self, keyword: str, limit: int = 10) -> list:
        """
        Fetches recent post titles from Reddit (r/stocks, r/investing, etc.)
        Uses the JSON interface.
        """
        # Search in relevant subreddits
        url = f"https://www.reddit.com/r/stocks+investing+wallstreetbets/search.json?q={keyword}&sort=new&restrict_sr=1&limit={limit}"
        titles = []
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        children = data.get('data', {}).get('children', [])
                        for child in children:
                            title = child.get('data', {}).get('title', '')
                            if title:
                                titles.append(title)
                    else:
                        logger.warning(f"Failed to fetch Reddit data for {keyword}: Status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching Reddit data for {keyword}: {e}")
            
        return titles

    async def fetch_yahoo_news(self, ticker: str, limit: int = 10) -> list:
        """
        Fetches recent news titles from Yahoo Finance RSS.
        """
        # Yahoo Finance RSS feed
        url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
        titles = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        soup = BeautifulSoup(xml_data, 'xml')
                        items = soup.find_all('item')
                        
                        for item in items[:limit]:
                            title = item.title.text if item.title else ""
                            if title:
                                titles.append(title)
                    else:
                        logger.warning(f"Failed to fetch Yahoo news for {ticker}: Status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching Yahoo news for {ticker}: {e}")
            
        return titles

    def analyze_text(self, text: str) -> float:
        """
        Analyzes text sentiment (supports KR and EN).
        Returns a score between -1.0 (Negative) and 1.0 (Positive).
        """
        score = 0.0
        text = text.lower()
        
        # Check Korean keywords
        for k in self.positive_keywords_kr:
            if k in text: score += 0.3
        for k in self.negative_keywords_kr:
            if k in text: score -= 0.3
            
        # Check English keywords
        for k in self.positive_keywords_en:
            if k in text: score += 0.3
        for k in self.negative_keywords_en:
            if k in text: score -= 0.3
                
        return max(-1.0, min(1.0, score))

    async def get_sentiment_score(self, code: str, ticker_symbol: str = None) -> float:
        """
        Calculates the aggregate sentiment score for a stock code.
        :param code: Korean stock code (e.g., '005930')
        :param ticker_symbol: US/Global ticker symbol (e.g., 'SSNLF' or just usage of code if applicable)
                              If None, tries to map or just uses code for KR news.
        """
        tasks = [self.fetch_news_titles_kr(code)]
        
        # If a ticker symbol is provided (or we want to search global sources for the code)
        # For Korean stocks, often the code isn't enough for Reddit/Yahoo. 
        # We might need the company name or a mapped ticker.
        # For this implementation, we'll assume 'ticker_symbol' is passed if global search is needed.
        if ticker_symbol:
            tasks.append(self.fetch_reddit_posts(ticker_symbol))
            tasks.append(self.fetch_yahoo_news(ticker_symbol))
            
        results = await asyncio.gather(*tasks)
        
        all_titles = []
        for res in results:
            all_titles.extend(res)
        
        if not all_titles:
            return 0.0
            
        total_score = 0.0
        for title in all_titles:
            total_score += self.analyze_text(title)
            
        avg_score = total_score / len(all_titles)
        final_score = max(-1.0, min(1.0, avg_score))
        
        logger.info(f"Sentiment for {code}/{ticker_symbol}: {final_score:.2f} (based on {len(all_titles)} items)")
        return final_score

if __name__ == "__main__":
    async def test():
        analyzer = SentimentAnalyzer()
        # Test Samsung Electronics (KR: 005930, Global: Samsung)
        print("Analyzing Samsung Electronics...")
        score = await analyzer.get_sentiment_score("005930", "Samsung Electronics")
        print(f"Score: {score}")
        
        # Test Tesla (if we were to use it, though code might be different)
        # print("Analyzing Tesla...")
        # score = await analyzer.get_sentiment_score("TSLA", "TSLA") # Hypothetical usage
        # print(f"Score: {score}")

    asyncio.run(test())
