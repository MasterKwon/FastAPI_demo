import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    """테스트 클라이언트 fixture"""
    return TestClient(app)

@pytest.fixture
def test_user():
    """테스트용 사용자 데이터 fixture"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    } 