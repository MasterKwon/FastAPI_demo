"""
데이터베이스 스키마 정의
"""
import os
from pathlib import Path

# 스키마 파일 디렉토리
SCHEMA_DIR = Path(__file__).parent

# 모든 스키마 파일 읽기
def read_schema_file(filename: str) -> str:
    """스키마 파일을 읽어서 반환합니다."""
    with open(SCHEMA_DIR / filename, 'r', encoding='utf-8') as f:
        return f.read()

# 모든 테이블 생성 쿼리 (마이그레이션 파일에서 읽기)
CREATE_ALL_TABLES = read_schema_file('../migrations/001_initial_schema.sql') 