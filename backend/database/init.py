"""
데이터베이스 초기화 및 연결 관리
"""

import logging
from pathlib import Path
from typing import AsyncGenerator
from backend.database.pool import db_pool

logger = logging.getLogger(__name__)

# 마이그레이션 디렉토리 경로
migrations_dir = Path(__file__).parent / "migrations"

def read_sql_file(file_path: Path) -> str:
    """SQL 파일을 읽어서 내용을 반환합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"SQL 파일 읽기 실패: {str(e)}")
        raise

def get_table_list(cur) -> set:
    """현재 데이터베이스의 테이블 목록을 반환합니다."""
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'vibecoding'
    """)
    return {row['table_name'] for row in cur.fetchall()}

def init_db():
    """데이터베이스를 초기화합니다."""
    try:
        # 디렉토리 존재 확인
        if not migrations_dir.exists():
            logger.error(f"마이그레이션 디렉토리가 존재하지 않습니다: {migrations_dir}")
            return
        
        # 초기 테이블 목록 저장
        with db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                initial_tables = get_table_list(cur)
        
        # 마이그레이션 파일 실행
        migration_files = sorted(migrations_dir.glob("*.sql"))
        for migration_file in migration_files:
            sql_content = read_sql_file(migration_file)
            with db_pool.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_content)
            conn.commit()
        
        # 최종 테이블 목록 확인 및 변경사항 로깅
        with db_pool.get_connection() as conn:
            with conn.cursor() as cur:
                final_tables = get_table_list(cur)
                
                # 새로 생성된 테이블
                new_tables = final_tables - initial_tables
                if new_tables:
                    logger.info(f"새로 생성된 테이블: {sorted(new_tables)}")
                
                # 삭제된 테이블
                deleted_tables = initial_tables - final_tables
                if deleted_tables:
                    logger.info(f"삭제된 테이블: {sorted(deleted_tables)}")
            
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {str(e)}")
        raise 