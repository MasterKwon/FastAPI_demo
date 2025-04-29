"""
전역 예외 처리기 모듈
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.database.exceptions import DatabaseError
from app.utils.logger import logger

async def database_exception_handler(request: Request, exc: DatabaseError):
    """데이터베이스 예외 처리"""
    logger.error(f"데이터베이스 오류: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "데이터베이스 오류가 발생했습니다."}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"서버 오류: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 오류가 발생했습니다."}
    )

exception_handlers = {
    DatabaseError: database_exception_handler,
    Exception: general_exception_handler
} 