"""
설정 모듈
"""
from pydantic import BaseSettings
from typing import Optional
import os
from pathlib import Path
import secrets

class Settings(BaseSettings):
    # 데이터베이스 설정
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_SCHEMA: str
    DB_USER: str
    DB_PASSWORD: str
    
    # 데이터베이스 연결 풀 설정
    DB_MIN_CONN: int = 2
    DB_MAX_CONN: int = 10  # CPU 코어 수에 따라 조정
    
    # 연결 타임아웃 설정 추가
    DB_CONNECT_TIMEOUT: int = 30  # 초 단위
    DB_POOL_TIMEOUT: int = 30  # 초 단위
    
    # JWT 설정
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 로깅 설정
    LOG_DIR: str = "logs"
    LOG_RETENTION_DAYS: int = 7
    
    # # 캐시 설정 (Redis)
    # REDIS_HOST: str
    # REDIS_PORT: int
    # REDIS_DB: int = 0
    # CACHE_TTL: int = 60  # 캐시 유효 시간(초)

    # 라우터 버전별 엔드포인트 관리
    API_V1_STR: str = "/api/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """데이터베이스 연결 URL을 생성합니다."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?options=-c%20search_path%3D{self.DB_SCHEMA}"

    # @property
    # def redis_url(self) -> str:
    #     """Redis 연결 URL을 생성합니다."""
    #     return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

# 환경 변수 파일 존재 여부 확인
env_file = Path(".env")
if not env_file.exists():
    raise FileNotFoundError(
        ".env 파일이 존재하지 않습니다. "
        "프로젝트 루트 디렉토리에 .env 파일을 생성하고 필요한 환경 변수를 설정해주세요."
    )

# 설정 인스턴스 생성
settings = Settings() 