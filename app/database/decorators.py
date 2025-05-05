"""
데이터베이스 데코레이터 모듈
"""
from functools import wraps
from app.database.exceptions import DatabaseError
from app.utils.logger import app_logger, LogType
import logging

def with_transaction(func):
    """
    트랜잭션을 관리하는 데코레이터
    
    Args:
        func: 데코레이트할 함수
        
    Returns:
        wrapper: 트랜잭션 관리 기능이 추가된 함수
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db = kwargs.get('db')
        if not db:
            raise DatabaseError("데이터베이스 연결이 없습니다.")
            
        try:
            result = await func(*args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            app_logger.log(
                logging.ERROR,
                f"트랜잭션 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"트랜잭션 실패: {str(e)}")
    return wrapper 