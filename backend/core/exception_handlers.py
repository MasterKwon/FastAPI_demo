"""
전역 예외 처리기 모듈
"""
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from backend.database.exceptions import DatabaseError
from backend.utils.logger import logger, LogType
import logging

async def database_exception_handler(request: Request, exc: DatabaseError):
    """데이터베이스 예외 처리"""
    logger.log(
        logging.ERROR,
        f"데이터베이스 오류: {str(exc)}",
        log_type=LogType.ALL
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "데이터베이스 오류가 발생했습니다."}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.log(
        logging.ERROR,
        f"서버 오류: {str(exc)}",
        log_type=LogType.ALL
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 오류가 발생했습니다."}
    )

exception_handlers = {
    DatabaseError: database_exception_handler,
    Exception: general_exception_handler
}

def setup_exception_handlers(app: FastAPI):
    """
    예외 처리기를 설정합니다.
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    for exception, handler in exception_handlers.items():
        app.add_exception_handler(exception, handler) 