"""
로깅 시스템 - 통합 로거 설정
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


# 로그 색상 코드 (ANSI)
class LogColors:
    """로그 레벨별 색상"""
    RESET = '\033[0m'
    DEBUG = '\033[36m'      # Cyan
    INFO = '\033[32m'       # Green
    WARNING = '\033[33m'    # Yellow
    ERROR = '\033[31m'      # Red
    CRITICAL = '\033[35m'   # Magenta


class ColoredFormatter(logging.Formatter):
    """색상이 있는 로그 포맷터"""
    
    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }
    
    def format(self, record):
        # 레벨에 따라 색상 추가
        levelname = record.levelname
        if record.levelno in self.COLORS:
            colored_levelname = f"{self.COLORS[record.levelno]}{levelname}{LogColors.RESET}"
            record.levelname = colored_levelname
        
        # 포맷 적용
        result = super().format(record)
        
        # 레벨명 복원
        record.levelname = levelname
        
        return result


def setup_logger(name='UpbitTrader', log_file=None, level=logging.INFO, 
                 max_bytes=10*1024*1024, backup_count=5):
    """
    로거 설정
    
    Args:
        name: 로거 이름
        log_file: 로그 파일 경로
        level: 로그 레벨
        max_bytes: 로그 파일 최대 크기 (기본: 10MB)
        backup_count: 백업 파일 개수
        
    Returns:
        logging.Logger: 설정된 로거
    """
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 포맷 정의
    console_format = '%(levelname)-8s │ %(message)s'
    file_format = '%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 콘솔 핸들러 (색상 포맷)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(console_format, datefmt=date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (로그 파일이 지정된 경우)
    if log_file:
        # 로그 디렉토리 생성
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일 핸들러 (자동 순환)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(file_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name='UpbitTrader'):
    """
    기존 로거 가져오기
    
    Args:
        name: 로거 이름
        
    Returns:
        logging.Logger: 로거 인스턴스
    """
    return logging.getLogger(name)


# 전역 로거 인스턴스
logger = setup_logger(
    name='UpbitTrader',
    log_file='./logs/trader.log',
    level=logging.INFO
)


if __name__ == "__main__":
    # 테스트
    print("=" * 60)
    print("📝 로깅 시스템 테스트")
    print("=" * 60)
    
    test_logger = setup_logger('TestLogger', './logs/test.log', logging.DEBUG)
    
    test_logger.debug("디버그 메시지 - 상세한 개발 정보")
    test_logger.info("정보 메시지 - 일반 정보")
    test_logger.warning("경고 메시지 - 주의 필요")
    test_logger.error("에러 메시지 - 오류 발생")
    test_logger.critical("심각 메시지 - 치명적 오류")
    
    print("\n✅ 로그 파일 생성됨: ./logs/test.log")
    print("✅ 색상 포맷 적용됨 (콘솔)")
