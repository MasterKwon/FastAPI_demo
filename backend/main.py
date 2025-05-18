"""
FastAPI 애플리케이션의 메인 모듈
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.user_router import router as user_router
from backend.routers.item_router import router as item_router
from backend.routers.item_review_router import router as review_router
from backend.routers.common_router import router as common_router
from backend.utils.logger import setup_logger, app_logger, LogType
from backend.database.init import init_db
from backend.core.middleware import RequestLoggingMiddleware
from backend.core.exception_handlers import setup_exception_handlers
import logging

# 로거 설정
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리
    """
    # 시작
    app_logger.log(
        logging.INFO,
        "애플리케이션 시작",
        log_type=LogType.ALL
    )
    init_db()
    yield
    # 종료
    app_logger.log(
        logging.INFO,
        "애플리케이션 종료",
        log_type=LogType.ALL
    )

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="FastAPI Demo",
    description="FastAPI를 사용한 데모 애플리케이션",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 특정 도메인만 허용하도록 수정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 로깅 미들웨어 추가
app.add_middleware(RequestLoggingMiddleware)

# 예외 핸들러 설정
setup_exception_handlers(app)

# 라우터 등록
app.include_router(common_router)  # 공통 라우터를 먼저 등록
app.include_router(user_router)
app.include_router(item_router)
app.include_router(review_router)

@app.get("/")
async def root():
    """
    루트 엔드포인트
    """
    return {"message": "Welcome to FastAPI Demo"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9123) 