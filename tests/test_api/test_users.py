import pytest
from fastapi import status

def test_create_user(client, test_user):
    """사용자 생성 테스트"""
    response = client.post("/api/v1/users/", json=test_user)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "password" not in data  # 비밀번호는 응답에 포함되지 않아야 함

def test_get_user(client, test_user):
    """사용자 조회 테스트"""
    # 먼저 사용자 생성
    create_response = client.post("/api/v1/users/", json=test_user)
    user_id = create_response.json()["id"]
    
    # 사용자 조회
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]

def test_update_user(client, test_user):
    """사용자 정보 수정 테스트"""
    # 먼저 사용자 생성
    create_response = client.post("/api/v1/users/", json=test_user)
    user_id = create_response.json()["id"]
    
    # 수정할 데이터
    update_data = {
        "username": "updateduser",
        "email": "updated@example.com"
    }
    
    # 사용자 정보 수정
    response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == update_data["username"]
    assert data["email"] == update_data["email"]

def test_delete_user(client, test_user):
    """사용자 삭제 테스트"""
    # 먼저 사용자 생성
    create_response = client.post("/api/v1/users/", json=test_user)
    user_id = create_response.json()["id"]
    
    # 사용자 삭제
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # 삭제된 사용자 조회 시도
    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND 