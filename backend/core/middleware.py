"""
미들웨어 모듈
"""
from time import time
from fastapi import Request
from backend.utils.logger import logger

async def performance_middleware(request: Request, call_next):
    """
    성능 모니터링 미들웨어
    
    Args:
        request: FastAPI 요청 객체
        call_next: 다음 미들웨어 또는 라우트 핸들러를 호출하는 함수
        
    Returns:
        response: FastAPI 응답 객체
    """
    start_time = time()
    
    try:
        response = await call_next(request)
        process_time = time() - start_time
        
        # 성능 로깅
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Time: {process_time:.2f}s - "
            f"Status: {response.status_code}"
        )
        
        return response
    except Exception as e:
        process_time = time() - start_time
        logger.error(
            f"Request: {request.method} {request.url.path} - "
            f"Time: {process_time:.2f}s - "
            f"Error: {str(e)}"
        )
        raise 