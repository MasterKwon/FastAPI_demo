"""
데이터베이스 예외 처리 모듈
"""

from fastapi import HTTPException
from psycopg2 import Error as PostgresError
from app.utils.logger import log_error

class DatabaseError(Exception):
    """데이터베이스 관련 기본 예외 클래스"""
    def __init__(self, message: str, query: str = None, params: dict = None):
        self.message = message
        self.query = query
        self.params = params
        super().__init__(self.message)

def handle_database_error(e: Exception, query: str = None, params: dict = None) -> None:
    """
    데이터베이스 예외를 처리하고 로깅
    
    Args:
        e: 발생한 예외 객체
        query: 실행 중이던 SQL 쿼리 (선택적)
        params: 쿼리 파라미터 (선택적)
    
    Raises:
        HTTPException: HTTP 500 에러
    """
    # 예외 로깅
    log_error(e, query, params)
    
    # HTTP 예외 발생
    if isinstance(e, PostgresError):
        raise HTTPException(
            status_code=500,
            detail=f"데이터베이스 오류: {str(e)}"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail=f"서버 오류: {str(e)}"
        ) 