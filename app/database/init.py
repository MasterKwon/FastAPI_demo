"""
데이터베이스 초기화 모듈
"""

import logging
import os
from pathlib import Path
from app.database.connection import get_db_connection
from app.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

def read_sql_file(file_path: str) -> str:
    """SQL 파일을 읽어서 내용을 반환합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"SQL 파일 읽기 실패: {e}")
        raise

def init_db():
    """
    데이터베이스 테이블을 초기화합니다.
    """
    try:
        logger.info("데이터베이스 초기화 시작")
        
        # 스키마 파일 경로
        schema_dir = Path(__file__).parent / "schemas"
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 스키마 파일 실행
            for schema_file in schema_dir.glob("*.sql"):
                logger.info(f"{schema_file.name} 스키마 실행 시도")
                sql_content = read_sql_file(schema_file)
                cursor.execute(sql_content)
                logger.info(f"{schema_file.name} 스키마 실행 완료")
            
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