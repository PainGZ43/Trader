"""
에러 핸들러 - 커스텀 예외 및 에러 처리
"""
import traceback
from functools import wraps
from typing import Callable, Any
import time


# === 커스텀 예외 클래스 ===

class UpbitAPIError(Exception):
    """Upbit API 관련 에러"""
    pass


class InsufficientBalanceError(Exception):
    """잔고 부족 에러"""
    pass


class OrderExecutionError(Exception):
    """주문 실행 에러"""
    pass


class DatabaseError(Exception):
    """데이터베이스 에러"""
    pass


class ConfigurationError(Exception):
    """설정 에러"""
    pass


class ModelError(Exception):
    """AI 모델 에러"""
    pass


# === 에러 처리 데코레이터 ===

def handle_errors(max_retries: int = 3, delay: float = 1.0, 
                  exceptions: tuple = (Exception,), 
                  logger=None):
    """
    에러 처리 및 재시도 데코레이터
    
    Args:
        max_retries: 최대 재시도 횟수
        delay: 재시도 간 대기 시간 (초)
        exceptions: 처리할 예외 튜플
        logger: 로거 인스턴스
        
    Usage:
        @handle_errors(max_retries=3, delay=1.0)
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if logger:
                        logger.warning(
                            f"{func.__name__} 실패 (시도 {attempt + 1}/{max_retries}): {e}"
                        )
                    
                    if attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # 지수 백오프
                    else:
                        if logger:
                            logger.error(
                                f"{func.__name__} 최종 실패: {e}\n"
                                f"{traceback.format_exc()}"
                            )
                        raise last_exception
            
            return None
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, default=None, logger=None, **kwargs) -> Any:
    """
    안전한 함수 실행 (에러 발생 시 기본값 반환)
    
    Args:
        func: 실행할 함수
        *args: 함수 인자
        default: 에러 시 반환할 기본값
        logger: 로거 인스턴스
        **kwargs: 함수 키워드 인자
        
    Returns:
        함수 실행 결과 또는 기본값
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if logger:
            logger.error(f"{func.__name__} 실행 에러: {e}")
        return default


class ErrorHandler:
    """중앙 에러 핸들러"""
    
    def __init__(self, logger=None):
        """
        Args:
            logger: 로거 인스턴스
        """
        self.logger = logger
        self.error_count = 0
        self.last_error = None
    
    def handle(self, error: Exception, context: str = ""):
        """
        에러 처리
        
        Args:
            error: 발생한 예외
            context: 에러 컨텍스트 (어디서 발생했는지)
        """
        self.error_count += 1
        self.last_error = error
        
        error_msg = f"[{context}] {type(error).__name__}: {str(error)}"
        
        if self.logger:
            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())
        else:
            print(f"❌ ERROR: {error_msg}")
    
    def reset(self):
        """에러 카운터 리셋"""
        self.error_count = 0
        self.last_error = None
    
    def get_status(self):
        """에러 상태 조회"""
        return {
            'error_count': self.error_count,
            'last_error': str(self.last_error) if self.last_error else None
        }


if __name__ == "__main__":
    # 테스트
    from utils.logger import setup_logger
    
    logger = setup_logger('ErrorHandlerTest', './logs/error_test.log')
    error_handler = ErrorHandler(logger)
    
    print("=" * 60)
    print("🔧 에러 핸들러 테스트")
    print("=" * 60)
    
    # 1. 커스텀 예외 테스트
    try:
        raise UpbitAPIError("API 연결 실패")
    except UpbitAPIError as e:
        error_handler.handle(e, "API 테스트")
    
    # 2. 재시도 데코레이터 테스트
    @handle_errors(max_retries=3, delay=0.5, logger=logger)
    def unstable_function(fail_count=2):
        """불안정한 함수 시뮬레이션"""
        if unstable_function.calls < fail_count:
            unstable_function.calls += 1
            raise ConnectionError(f"연결 실패 ({unstable_function.calls})")
        return "성공!"
    
    unstable_function.calls = 0
    result = unstable_function(fail_count=2)
    print(f"\n✅ 재시도 성공: {result}")
    
    # 3. safe_execute 테스트
    def risky_function():
        raise ValueError("의도된 에러")
    
    result = safe_execute(risky_function, default="기본값", logger=logger)
    print(f"✅ 안전 실행 결과: {result}")
    
    # 4. 에러 상태 조회
    status = error_handler.get_status()
    print(f"\n📊 에러 상태: {status}")
