"""
데이터베이스 연결 관리
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings

def get_db_connection():
    """데이터베이스 연결을 반환합니다."""
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        cursor_factory=RealDictCursor,
        options=f"-c search_path={settings.DB_SCHEMA}"
    )
    
    # 자동 커밋 비활성화
    conn.autocommit = False
    return conn 