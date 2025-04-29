"""
데이터베이스 초기화 모듈
"""

import logging
from app.database.connection import get_db_connection
from app.database.schemas import CREATE_ITEMS_TABLE, CREATE_USERS_TABLE
from app.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

def init_db():
    """
    데이터베이스 테이블을 초기화합니다.
    """
    try:
        logger.info("데이터베이스 초기화 시작")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Users 테이블 생성
            logger.info("Users 테이블 생성 시도")
            cursor.execute(CREATE_USERS_TABLE)
            logger.info("Users 테이블 생성 완료")
            
            # Items 테이블 생성
            logger.info("Items 테이블 생성 시도")
            cursor.execute(CREATE_ITEMS_TABLE)
            logger.info("Items 테이블 생성 완료")
            
            # 변경사항 커밋
            logger.info("변경사항 커밋 시도")
            conn.commit()
            logger.info("변경사항 커밋 완료")
            
            # 테이블 생성 확인
            cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{settings.DB_SCHEMA}'")
            tables = cursor.fetchall()
            logger.info(f"생성된 테이블 목록: {[table['table_name'] for table in tables]}")
            
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
        if 'conn' in locals():
            conn.rollback()
            logger.info("변경사항 롤백 완료")
        raise 