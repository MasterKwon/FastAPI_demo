"""
비동기 데이터베이스 연결 풀 모듈
"""
import asyncpg
from backend.config import settings
from fastapi import Depends
from typing import AsyncGenerator

class AsyncDatabasePool:
    """비동기 데이터베이스 연결 풀 클래스"""
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncDatabasePool, cls).__new__(cls)
        return cls._instance

    async def initialize(self):
        """비동기 데이터베이스 연결 풀을 초기화합니다."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                min_size=settings.DB_MIN_CONN,
                max_size=settings.DB_MAX_CONN,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                command_timeout=settings.DB_CONNECT_TIMEOUT,
                server_settings={
                    'search_path': settings.DB_SCHEMA
                }
            )

    async def get_connection(self):
        """비동기 데이터베이스 연결을 가져옵니다."""
        if self._pool is None:
            await self.initialize()
        return await self._pool.acquire()

    async def put_connection(self, conn):
        """비동기 데이터베이스 연결을 반환합니다."""
        await self._pool.release(conn)

    async def close_all(self):
        """모든 비동기 데이터베이스 연결을 닫습니다."""
        if self._pool:
            await self._pool.close()
            self._pool = None

# 싱글톤 인스턴스 생성
async_db_pool = AsyncDatabasePool()

async def get_async_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    FastAPI 의존성 주입을 위한 비동기 데이터베이스 연결 반환 함수
    """
    conn = await async_db_pool.get_connection()
    try:
        yield conn
    finally:
        await async_db_pool.put_connection(conn) 