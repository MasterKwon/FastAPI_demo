"""
미들웨어 모듈
"""
from time import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.utils.logger import logger, LogType
import logging

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청 로깅 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        """
        요청을 처리하고 로깅합니다.
        
        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어 또는 라우트 핸들러를 호출하는 함수
            
        Returns:
            response: FastAPI 응답 객체
        """
        start_time = time()
        
        try:
            # 요청 로깅
            logger.log(
                logging.INFO,
                f"Request: {request.method} {request.url.path}",
                log_type=LogType.ALL
            )
            
            response = await call_next(request)
            process_time = time() - start_time
            
            # 응답 로깅
            logger.log(
                logging.INFO,
                f"Response: {request.method} {request.url.path} - "
                f"Time: {process_time:.2f}s - "
                f"Status: {response.status_code}",
                log_type=LogType.ALL
            )
            
            return response
        except Exception as e:
            process_time = time() - start_time
            logger.log(
                logging.ERROR,
                f"Error: {request.method} {request.url.path} - "
                f"Time: {process_time:.2f}s - "
                f"Error: {str(e)}",
                log_type=LogType.ALL
            )
            raise 