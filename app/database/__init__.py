"""
데이터베이스 초기화 및 연결 관리
"""
import logging
from typing import AsyncGenerator
from .pool import db_pool
from .schemas import CREATE_ALL_TABLES

logger = logging.getLogger(__name__)

async def init_db() -> None:
    """데이터베이스 초기화 및 테이블 생성"""
    try:
        # 테이블 생성
        conn = db_pool.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(CREATE_ALL_TABLES)
                conn.commit()
            logger.info("데이터베이스 테이블 생성 완료")
        finally:
            db_pool.put_connection(conn)
            
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {str(e)}")
        raise

async def get_db() -> AsyncGenerator:
    """데이터베이스 연결 획득"""
    conn = db_pool.get_connection()
    try:
        yield conn
    except Exception as e:
        logger.error(f"데이터베이스 연결 오류: {str(e)}")
        raise
    finally:
        db_pool.put_connection(conn) 