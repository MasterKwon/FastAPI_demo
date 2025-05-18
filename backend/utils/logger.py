"""
로깅 유틸리티
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Union, Any
from functools import wraps
from enum import Enum
from datetime import datetime
from backend.core.config import settings

# 로그 타입 정의
class LogType(Enum):
    ALL = "A"  # 모든 출력
    FILE = "F"  # 파일 출력만
    CONSOLE = "C"  # 콘솔 출력만

# 로그 디렉토리 설정
log_dir = settings.LOG_DIR
os.makedirs(log_dir, exist_ok=True)

# 로그 파일 경로 설정
def get_log_file():
    current_date = datetime.now().strftime('%Y%m%d')
    return os.path.join(log_dir, f"{settings.SERVICE_NAME}_{current_date}.log")

# 기존 setup_logger 함수 유지
def setup_logger(name=None):
    """
    기존 방식의 로거 설정 (하위 호환성 유지)
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    file_handler = RotatingFileHandler(
        get_log_file(),
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] [%(module)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_query(cursor, query, params=None):
    """
    SQL 쿼리를 로깅합니다.
    """
    # 데이터베이스 로거 설정
    db_logger = setup_logger('database')
    db_logger.setLevel(logging.DEBUG)
    
    try:
        formatted_query = cursor.mogrify(query, params).decode('utf-8')
        db_logger.debug(f"[DB] 실행 쿼리: {formatted_query}")
    except Exception as e:
        db_logger.error(f"[DB] 쿼리 로깅 실패: {str(e)}")

# 새로운 로깅 시스템
class AppLogger:
    _instance = None
    _file_handler = None
    _console_handler = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        """로거 초기 설정"""
        self.logger = logging.getLogger("app")
        self.logger.setLevel(logging.INFO)
        
        # 포맷터 설정
        self.formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] [%(module)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 파일 핸들러 설정
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        self._file_handler = RotatingFileHandler(
            get_log_file(),
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        self._file_handler.setFormatter(self.formatter)
        
        # 콘솔 핸들러 설정
        self._console_handler = logging.StreamHandler()
        self._console_handler.setFormatter(self.formatter)
    
    def _update_log_file(self):
        """일자 변경 시 로그 파일 업데이트"""
        new_log_file = get_log_file()
        current_file = self._file_handler.baseFilename
        
        if new_log_file != current_file:
            # 새로운 파일 핸들러 생성
            new_file_handler = RotatingFileHandler(
                new_log_file,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            new_file_handler.setFormatter(self.formatter)
            
            # 기존 핸들러 제거 및 새 핸들러 추가
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = new_file_handler
            self.logger.addHandler(self._file_handler)
    
    def log(self, 
            level: int,
            message: Any,
            log_type: LogType = LogType.ALL,
            *args, **kwargs):
        """
        지정된 출력 방식으로 로그를 기록합니다.
        
        Args:
            level: 로그 레벨 (logging.INFO, logging.ERROR 등)
            message: 로그 메시지
            log_type: 로그 출력 타입 (A: 모두, F: 파일만, C: 콘솔만)
        """
        # 일자 변경 확인 및 로그 파일 업데이트
        self._update_log_file()
        
        # 임시 로거 생성
        temp_logger = logging.getLogger(f"temp_{id(message)}")
        temp_logger.setLevel(level)
        
        # 기존 핸들러 제거
        for handler in temp_logger.handlers[:]:
            temp_logger.removeHandler(handler)
        
        # 요청된 핸들러만 추가
        if log_type in [LogType.ALL, LogType.FILE]:
            temp_logger.addHandler(self._file_handler)
        if log_type in [LogType.ALL, LogType.CONSOLE]:
            temp_logger.addHandler(self._console_handler)
        
        # 로그 기록
        temp_logger.log(level, message, *args, **kwargs)
        
        # 핸들러 제거
        for handler in temp_logger.handlers[:]:
            temp_logger.removeHandler(handler)

def log_operation(log_type: LogType = LogType.ALL):
    """
    함수의 실행을 로깅하는 데코레이터
    
    Args:
        log_type: 로그 출력 타입 (A: 모두, F: 파일만, C: 콘솔만)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            try:
                # 함수 시작 로그
                app_logger.log(
                    logging.INFO,
                    f"Starting {func_name}",
                    log_type=log_type
                )
                
                # 함수 실행
                result = await func(*args, **kwargs)
                
                # 함수 완료 로그
                app_logger.log(
                    logging.INFO,
                    f"Completed {func_name}",
                    log_type=log_type
                )
                
                return result
                
            except Exception as e:
                # 에러 로그
                app_logger.log(
                    logging.ERROR,
                    f"Error in {func_name}: {str(e)}",
                    log_type=log_type
                )
                raise
        return wrapper
    return decorator

def log_error(e: Exception, query: str = None, params: dict = None):
    """
    예외 상황을 로깅
    
    Args:
        e: 발생한 예외 객체
        query: 실행 중이던 SQL 쿼리 (선택적)
        params: 쿼리 파라미터 (선택적)
    """
    # 호출 스택에서 파일 경로와 라인 번호 가져오기
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    file_path = caller_frame.f_code.co_filename
    line_number = caller_frame.f_lineno
    
    # 상대 경로로 변환
    try:
        relative_path = Path(file_path).relative_to(Path(__file__).parent.parent.parent)
    except ValueError:
        relative_path = file_path

    # 예외 정보 로깅
    logger.error(f"[{relative_path}:{line_number}] 예외 발생: {str(e)}")
    logger.error(f"[{relative_path}:{line_number}] 예외 타입: {type(e).__name__}")
    logger.error(f"[{relative_path}:{line_number}] 스택 트레이스:\n{traceback.format_exc()}")

    # 쿼리 정보가 있는 경우 로깅
    if query:
        logger.error(f"[{relative_path}:{line_number}] 실패한 쿼리: {query}")
        if params:
            logger.error(f"[{relative_path}:{line_number}] 쿼리 파라미터: {params}")

# 전역 로거 인스턴스
app_logger = AppLogger()

# 기존 코드와의 호환성을 위한 logger 인스턴스
logger = setup_logger("app") 