"""
공통 기능을 제공하는 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.schemas.common import ResponseModel
from backend.core.config import settings
from backend.utils.decorators import log_operation
from backend.database.async_pool import get_async_db, async_db_pool
from backend.utils.log_reader import LogReader
from backend.utils.stats_collector import StatsCollector
from backend.utils.cache_manager import CacheManager
from sqlalchemy.orm import Session
import psutil
import platform
from backend.utils.logger import LogType
import asyncpg
import logging

# 로거 설정
logger = setup_logger(__name__)

router = APIRouter(
    prefix="/common",
    tags=["common"],
    responses={404: {"description": "Not found"}},
)

@router.get("/health", response_model=ResponseModel[Dict[str, Any]])
@log_operation(log_type=LogType.ALL)
async def health_check():
    """
    서버 상태를 확인합니다.
    
    Returns:
        서버 상태 정보
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 데이터베이스 연결 확인
            await async_db_pool.execute_query(
                conn,
                "SELECT 1"
            )
            
            app_logger.log(
                logging.INFO,
                "[COMMON_ROUTER] 헬스 체크 완료",
                log_type=LogType.ALL
            )
            
            return ResponseModel(
                data={
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat()
                },
                message="Server is healthy"
            )
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[COMMON_ROUTER] 헬스 체크 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/info", response_model=ResponseModel[Dict[str, Any]])
@log_operation(log_type=LogType.ALL)
async def system_info():
    """
    시스템 정보 조회
    """
    info = {
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "start_time": settings.START_TIME.isoformat(),
        "uptime": str(datetime.utcnow() - settings.START_TIME)
    }
    
    return ResponseModel(
        success=True,
        message="System information retrieved",
        data=info
    )

@router.get("/logs", response_model=ResponseModel[List[Dict[str, Any]]])
@log_operation(log_type=LogType.ALL)
async def get_logs(
    level: str = "INFO",
    limit: int = 100,
    skip: int = 0
):
    """
    시스템 로그 조회
    - level: 로그 레벨 (INFO, WARNING, ERROR, DEBUG, ALL)
    - limit: 조회할 로그 수
    - skip: 건너뛸 로그 수
    """
    log_reader = LogReader()
    logs = log_reader.read_logs(level=level, limit=limit, skip=skip)
    
    return ResponseModel(
        success=True,
        message="Logs retrieved successfully",
        data=logs
    )

@router.get("/cache/status", response_model=ResponseModel[Dict[str, Any]])
@log_operation(log_type=LogType.ALL)
async def cache_status():
    """
    캐시 상태 확인
    - 캐시 타입 (Redis/Memory)
    - 사용 중인 메모리
    - 연결된 클라이언트 수
    - 총 키 수
    - 가동 시간
    - 마지막 저장 시간
    """
    cache_manager = CacheManager()
    stats = cache_manager.get_cache_stats()
    
    return ResponseModel(
        success=True,
        message="Cache status retrieved successfully",
        data=stats
    )

@router.post("/cache/clear", response_model=ResponseModel)
@log_operation(log_type=LogType.ALL)
async def clear_cache():
    """
    캐시 초기화
    - 모든 캐시 데이터 삭제
    """
    cache_manager = CacheManager()
    success = cache_manager.clear_cache()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )
    
    return ResponseModel(
        success=True,
        message="Cache cleared successfully"
    )

@router.get("/cache/keys", response_model=ResponseModel[List[str]])
@log_operation(log_type=LogType.ALL)
async def get_cache_keys(
    pattern: str = Query("*", description="캐시 키 패턴")
):
    """
    캐시 키 목록 조회
    - pattern: 검색할 캐시 키 패턴
    """
    cache_manager = CacheManager()
    keys = cache_manager.get_cache_keys(pattern)
    
    return ResponseModel(
        success=True,
        message="Cache keys retrieved successfully",
        data=keys
    )

@router.delete("/cache/keys/{key}", response_model=ResponseModel)
@log_operation(log_type=LogType.ALL)
async def delete_cache_key(key: str):
    """
    특정 캐시 키 삭제
    - key: 삭제할 캐시 키
    """
    cache_manager = CacheManager()
    success = cache_manager.delete_cache_key(key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete cache key: {key}"
        )
    
    return ResponseModel(
        success=True,
        message=f"Cache key '{key}' deleted successfully"
    )

@router.get("/stats", response_model=ResponseModel[Dict[str, Any]])
@log_operation(log_type=LogType.ALL)
async def system_stats(db: Session = Depends(get_async_db)):
    """
    시스템 통계
    - 전체 사용자 수
    - 전체 아이템 수
    - 전체 리뷰 수
    - 활성 세션 수
    - 분당 요청 수
    """
    stats_collector = StatsCollector(db)
    stats = stats_collector.get_system_stats()
    
    return ResponseModel(
        success=True,
        message="System statistics retrieved successfully",
        data=stats
    )

@router.get("/tables")
@log_operation(log_type=LogType.ALL)
async def get_tables():
    """
    데이터베이스 테이블 목록을 조회합니다.
    
    Returns:
        테이블 목록
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 테이블 목록 조회
            rows = await async_db_pool.fetch(
                conn,
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            
            app_logger.log(
                logging.INFO,
                f"[COMMON_ROUTER] 테이블 목록 조회 완료: {len(rows)}개",
                log_type=LogType.ALL
            )
            
            return ResponseModel(
                data=[row['table_name'] for row in rows],
                message="Tables retrieved successfully"
            )
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[COMMON_ROUTER] 테이블 목록 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/tables/{table_name}/columns")
@log_operation(log_type=LogType.ALL)
async def get_table_columns(table_name: str = Path(..., description="테이블 이름")):
    """
    특정 테이블의 컬럼 정보를 조회합니다.
    
    Args:
        table_name: 조회할 테이블 이름
        
    Returns:
        컬럼 정보 목록
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 컬럼 정보 조회
            rows = await async_db_pool.fetch(
                conn,
                """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = $1
                ORDER BY ordinal_position
                """,
                table_name
            )
            
            if not rows:
                app_logger.log(
                    logging.WARNING,
                    f"[COMMON_ROUTER] 테이블을 찾을 수 없음: {table_name}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Table not found"
                )
            
            app_logger.log(
                logging.INFO,
                f"[COMMON_ROUTER] 컬럼 정보 조회 완료: {table_name} ({len(rows)}개)",
                log_type=LogType.ALL
            )
            
            return ResponseModel(
                data=[dict(row) for row in rows],
                message="Table columns retrieved successfully"
            )
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[COMMON_ROUTER] 컬럼 정보 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/tables/{table_name}/data")
@log_operation(log_type=LogType.ALL)
async def get_table_data(
    table_name: str = Path(..., description="테이블 이름"),
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수")
):
    """
    특정 테이블의 데이터를 조회합니다.
    
    Args:
        table_name: 조회할 테이블 이름
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        
    Returns:
        테이블 데이터
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 테이블 존재 확인
            exists = await async_db_pool.fetchrow(
                conn,
                """
                SELECT EXISTS(
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                )
                """,
                table_name
            )
            
            if not exists:
                app_logger.log(
                    logging.WARNING,
                    f"[COMMON_ROUTER] 테이블을 찾을 수 없음: {table_name}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Table not found"
                )
            
            # 데이터 조회
            rows = await async_db_pool.fetch(
                conn,
                f"SELECT * FROM {table_name} LIMIT $1 OFFSET $2",
                limit,
                skip
            )
            
            app_logger.log(
                logging.INFO,
                f"[COMMON_ROUTER] 테이블 데이터 조회 완료: {table_name} ({len(rows)}개)",
                log_type=LogType.ALL
            )
            
            return ResponseModel(
                data=[dict(row) for row in rows],
                message="Table data retrieved successfully"
            )
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[COMMON_ROUTER] 테이블 데이터 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 