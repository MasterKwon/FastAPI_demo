"""
FastAPI 메인 애플리케이션 모듈
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import performance_middleware
from app.core.exception_handlers import exception_handlers
from app.routers import users, items
from app.database.pool import db_pool
from app.config import settings

app = FastAPI(
    title="FastAPI Demo",
    description="FastAPI 데모 애플리케이션",
    version="1.0.0",
    exception_handlers=exception_handlers
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 성능 모니터링 미들웨어 추가
app.middleware("http")(performance_middleware)

# 라우터 등록
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(items.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup():
    """애플리케이션 시작 시 실행"""
    # 데이터베이스 연결 풀 초기화
    db_pool.__init__()

@app.on_event("shutdown")
async def shutdown():
    """애플리케이션 종료 시 실행"""
    # 데이터베이스 연결 풀 종료
    db_pool.close_all()

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "Welcome to FastAPI Demo"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9123) 