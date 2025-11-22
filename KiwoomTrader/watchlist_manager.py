"""
Watchlist Manager
관심종목 관리
"""
import json
import os
from logger import logger

class WatchlistManager:
    """관심종목 관리 클래스"""
    
    def __init__(self, filepath='data/watchlist.json'):
        self.filepath = filepath
        self.watchlist = []
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.load()
    
    def load(self):
        """관심종목 로드"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.watchlist = data.get('stocks', [])
                logger.info(f"Loaded {len(self.watchlist)} stocks from watchlist")
            except Exception as e:
                logger.error(f"Error loading watchlist: {e}")
                self.watchlist = []
        else:
            self.watchlist = []
    
    def save(self):
        """관심종목 저장"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump({'stocks': self.watchlist}, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.watchlist)} stocks to watchlist")
        except Exception as e:
            logger.error(f"Error saving watchlist: {e}")
    
    def add(self, stock_code, stock_name=''):
        """종목 추가"""
        # 중복 체크
        if any(s['code'] == stock_code for s in self.watchlist):
            logger.warning(f"{stock_code} already in watchlist")
            return False
        
        stock_info = {
            'code': stock_code,
            'name': stock_name
        }
        
        self.watchlist.append(stock_info)
        self.save()
        logger.info(f"Added {stock_code} to watchlist")
        return True
    
    def remove(self, stock_code):
        """종목 제거"""
        original_len = len(self.watchlist)
        self.watchlist = [s for s in self.watchlist if s['code'] != stock_code]
        
        if len(self.watchlist) < original_len:
            self.save()
            logger.info(f"Removed {stock_code} from watchlist")
            return True
        else:
            logger.warning(f"{stock_code} not found in watchlist")
            return False
    
    def get_all(self):
        """모든 관심종목 반환"""
        return self.watchlist.copy()
    
    def get_codes(self):
        """종목 코드 리스트만 반환"""
        return [s['code'] for s in self.watchlist]
    
    def clear(self):
        """모든 관심종목 제거"""
        self.watchlist = []
        self.save()
        logger.info("Cleared watchlist")
    
    def count(self):
        """관심종목 개수"""
        return len(self.watchlist)
