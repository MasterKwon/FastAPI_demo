"""
로깅 관련 데코레이터
"""
from functools import wraps
import logging
from typing import Callable, Any
from app.utils.logger import app_logger, LogType

def log_operation(log_type: LogType = LogType.ALL) -> Callable:
    """
    API 작업 로깅을 위한 데코레이터
    
    Args:
        log_type: 로그 출력 타입 (ALL: 모두, FILE: 파일만, CONSOLE: 콘솔만)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # 함수 시작 로깅
                app_logger.log(
                    logging.INFO,
                    f"작업 시작: {func.__name__}",
                    log_type=log_type
                )
                
                # 함수 실행
                result = await func(*args, **kwargs)
                
                # 함수 성공 로깅
                app_logger.log(
                    logging.INFO,
                    f"작업 완료: {func.__name__}",
                    log_type=log_type
                )
                
                return result
                
            except Exception as e:
                # 함수 실패 로깅
                app_logger.log(
                    logging.ERROR,
                    f"작업 실패: {func.__name__} - {str(e)}",
                    log_type=log_type
                )
                raise
                
        return wrapper
    return decorator

def log_database_operation(log_type: LogType = LogType.ALL) -> Callable:
    """
    데이터베이스 작업 로깅을 위한 데코레이터
    
    Args:
        log_type: 로그 출력 타입 (ALL: 모두, FILE: 파일만, CONSOLE: 콘솔만)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # 쿼리 시작 로깅
                app_logger.log(
                    logging.INFO,
                    f"DB 작업 시작: {func.__name__}",
                    log_type=log_type
                )
                
                # 쿼리 실행
                result = await func(*args, **kwargs)
                
                # 쿼리 성공 로깅
                app_logger.log(
                    logging.INFO,
                    f"DB 작업 완료: {func.__name__}",
                    log_type=log_type
                )
                
                return result
                
            except Exception as e:
                # 쿼리 실패 로깅
                app_logger.log(
                    logging.ERROR,
                    f"DB 작업 실패: {func.__name__} - {str(e)}",
                    log_type=log_type
                )
                raise
                
        return wrapper
    return decorator 