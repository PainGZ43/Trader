"""
설정 관리 모듈 - 전역 설정 및 환경 변수 관리
"""
from dotenv import load_dotenv
import os
from pathlib import Path


class Config:
    """전역 설정 관리 클래스"""
    
    def __init__(self):
        """설정 초기화"""
        # .env 파일 로드
        load_dotenv()
        
        # 프로젝트 루트 경로
        self.PROJECT_ROOT = Path(__file__).parent
        
        # API 설정
        self.UPBIT_ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY', '')
        self.UPBIT_SECRET_KEY = os.getenv('UPBIT_SECRET_KEY', '')
        
        # 경로 설정
        self.DB_PATH = os.getenv('DB_PATH', str(self.PROJECT_ROOT / 'database' / 'trading.db'))
        self.MODEL_PATH = os.getenv('MODEL_PATH', str(self.PROJECT_ROOT / 'models'))
        self.LOG_FILE = os.getenv('LOG_FILE', str(self.PROJECT_ROOT / 'logs' / 'trader.log'))
        self.DATA_CACHE_PATH = self.PROJECT_ROOT / 'data_cache'
        
        # 로그 설정
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # AI 모델 설정
        self.RETRAIN_INTERVAL_DAYS = int(os.getenv('RETRAIN_INTERVAL_DAYS', 7))
        
        # 트레이딩 설정
        self.MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 1000000))
        self.STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', 5.0))
        self.TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', 10.0))
        self.MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', 50))
        self.DAILY_LOSS_LIMIT = float(os.getenv('DAILY_LOSS_LIMIT', 100000))
        
        # 알림 설정
        self.ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'False').lower() == 'true'
        self.KAKAO_TOKEN = os.getenv('KAKAO_TOKEN', '')
        
        # 디렉토리 생성
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            Path(self.DB_PATH).parent,
            Path(self.MODEL_PATH),
            Path(self.LOG_FILE).parent,
            self.DATA_CACHE_PATH,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate(self):
        """설정 유효성 검증"""
        errors = []
        
        # API 키 검증
        if not self.UPBIT_ACCESS_KEY or self.UPBIT_ACCESS_KEY == 'your_access_key_here':
            errors.append("Upbit Access Key가 설정되지 않았습니다.")
        
        if not self.UPBIT_SECRET_KEY or self.UPBIT_SECRET_KEY == 'your_secret_key_here':
            errors.append("Upbit Secret Key가 설정되지 않았습니다.")
        
        # 숫자 범위 검증
        if self.STOP_LOSS_PERCENT < 0 or self.STOP_LOSS_PERCENT > 100:
            errors.append("손절률은 0-100 사이여야 합니다.")
        
        if self.TAKE_PROFIT_PERCENT < 0 or self.TAKE_PROFIT_PERCENT > 1000:
            errors.append("익절률은 0-1000 사이여야 합니다.")
        
        if errors:
            raise ValueError(f"설정 검증 실패:\n" + "\n".join(f"- {err}" for err in errors))
        
        return True
    
    def is_api_configured(self):
        """API 키 설정 여부 확인"""
        return (self.UPBIT_ACCESS_KEY and 
                self.UPBIT_ACCESS_KEY != 'your_access_key_here' and
                self.UPBIT_SECRET_KEY and 
                self.UPBIT_SECRET_KEY != 'your_secret_key_here')
    
    def __repr__(self):
        """설정 정보 출력"""
        return (f"Config(\n"
                f"  API Configured: {self.is_api_configured()}\n"
                f"  DB Path: {self.DB_PATH}\n"
                f"  Log Level: {self.LOG_LEVEL}\n"
                f"  Max Position Size: {self.MAX_POSITION_SIZE:,.0f} KRW\n"
                f"  Stop Loss: {self.STOP_LOSS_PERCENT}%\n"
                f"  Take Profit: {self.TAKE_PROFIT_PERCENT}%\n"
                f")")


# 전역 설정 인스턴스
config = Config()


if __name__ == "__main__":
    # 설정 테스트
    print("=" * 50)
    print("Configuration Info")
    print("=" * 50)
    print(config)
    
    try:
        if config.is_api_configured():
            config.validate()
            print("\n[OK] Configuration validation successful!")
        else:
            print("\n[WARNING] API keys not configured.")
            print("   Please create .env file and set your API keys.")
    except ValueError as e:
        print(f"\n[ERROR] {e}")
