"""
데이터베이스 연결 풀 모듈
"""
from psycopg2 import pool
from app.config import settings

class DatabasePool:
    """데이터베이스 연결 풀 클래스"""
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pool is None:
            self._pool = pool.ThreadedConnectionPool(
                minconn=settings.DB_MIN_CONN,
                maxconn=settings.DB_MAX_CONN,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD
            )

    def get_connection(self):
        """데이터베이스 연결을 가져옵니다."""
        return self._pool.getconn()

    def put_connection(self, conn):
        """데이터베이스 연결을 반환합니다."""
        self._pool.putconn(conn)

    def close_all(self):
        """모든 데이터베이스 연결을 닫습니다."""
        if self._pool:
            self._pool.closeall()
            self._pool = None

# 싱글톤 인스턴스 생성
db_pool = DatabasePool() 