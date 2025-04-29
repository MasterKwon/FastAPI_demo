"""
로깅 유틸리티
"""

import logging
import inspect
import traceback
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

def setup_logger(name: str, log_dir: str = None) -> logging.Logger:
    """
    로거 설정 함수
    
    Args:
        name: 로거 이름
        log_dir: 로그 파일이 저장될 디렉토리 (기본값: app/logs)
    
    Returns:
        설정된 로거 객체
    """
    if log_dir is None:
        # 기본 로그 디렉토리 설정
        log_dir = Path(__file__).parent.parent / "logs"
    
    # 로그 디렉토리 생성
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러 설정
    log_file = log_dir / f"{name}.log"
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    
    # 포맷터 설정
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    
    return logger

# 데이터베이스 로거 생성
db_logger = setup_logger('database')

# logger라는 이름으로도 사용할 수 있게 alias 추가
logger = db_logger

def log_query(cursor, query: str, params: dict = None):
    """
    SQL 쿼리 실행 로깅
    
    Args:
        cursor: 데이터베이스 커서
        query: 실행할 SQL 쿼리
        params: 쿼리 파라미터
    """
    logger.info(f"실행 쿼리: {query}")
    if params:
        logger.info(f"파라미터: {params}")

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