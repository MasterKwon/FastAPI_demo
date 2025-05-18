"""
비동기 데이터베이스 연결 풀 모듈
"""
import asyncpg
from backend.core.config import settings
from fastapi import Depends
from typing import AsyncGenerator, AsyncContextManager
from backend.utils.logger import app_logger, LogType
from backend.utils.decorators import log_database_operation
import logging
import time
from contextlib import asynccontextmanager

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

    @asynccontextmanager
    @log_database_operation(log_type=LogType.ALL)
    async def transaction(self, conn):
        """트랜잭션 컨텍스트 매니저를 제공합니다."""
        start_time = time.time()
        tr = conn.transaction()
        try:
            await tr.start()
            app_logger.log(
                logging.INFO,
                "[DB] Transaction started",
                log_type=LogType.ALL
            )
            yield tr
            await tr.commit()
            execution_time = time.time() - start_time
            app_logger.log(
                logging.INFO,
                f"[DB] Transaction committed successfully in {execution_time:.3f}s",
                log_type=LogType.ALL
            )
        except Exception as e:
            await tr.rollback()
            execution_time = time.time() - start_time
            app_logger.log(
                logging.ERROR,
                f"[DB] Transaction rolled back after {execution_time:.3f}s. Error: {str(e)}",
                log_type=LogType.ALL
            )
            raise

    @log_database_operation(log_type=LogType.ALL)
    async def execute_query(self, conn, query, *args, **kwargs):
        """쿼리를 실행하고 로깅합니다."""
        start_time = time.time()
        try:
            result = await conn.execute(query, *args, **kwargs)
            execution_time = time.time() - start_time
            app_logger.log(
                logging.INFO,
                f"[DB] Query executed successfully in {execution_time:.3f}s: {query[:100]}...",
                log_type=LogType.ALL
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            app_logger.log(
                logging.ERROR,
                f"[DB] Query failed after {execution_time:.3f}s: {query[:100]}... Error: {str(e)}",
                log_type=LogType.ALL
            )
            raise

    @log_database_operation(log_type=LogType.ALL)
    async def fetchrow(self, conn, query, *args, **kwargs):
        """단일 행을 조회하고 로깅합니다."""
        start_time = time.time()
        try:
            result = await conn.fetchrow(query, *args, **kwargs)
            execution_time = time.time() - start_time
            app_logger.log(
                logging.INFO,
                f"[DB] Fetchrow executed successfully in {execution_time:.3f}s: {query[:100]}...",
                log_type=LogType.ALL
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            app_logger.log(
                logging.ERROR,
                f"[DB] Fetchrow failed after {execution_time:.3f}s: {query[:100]}... Error: {str(e)}",
                log_type=LogType.ALL
            )
            raise

    @log_database_operation(log_type=LogType.ALL)
    async def fetch(self, conn, query, *args, **kwargs):
        """여러 행을 조회하고 로깅합니다."""
        start_time = time.time()
        try:
            result = await conn.fetch(query, *args, **kwargs)
            execution_time = time.time() - start_time
            app_logger.log(
                logging.INFO,
                f"[DB] Fetch executed successfully in {execution_time:.3f}s: {query[:100]}... Rows: {len(result)}",
                log_type=LogType.ALL
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            app_logger.log(
                logging.ERROR,
                f"[DB] Fetch failed after {execution_time:.3f}s: {query[:100]}... Error: {str(e)}",
                log_type=LogType.ALL
            )
            raise

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