"""
사용자 관련 모델 정의
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserSortColumn(str, Enum):
    """사용자 정렬 기준 컬럼"""
    id = "id"
    username = "username"
    email = "email"
    created_at = "created_at"

class SortDirection(str, Enum):
    """정렬 방향"""
    ASC = "ASC"
    DESC = "DESC"

class UserBase(BaseModel):
    """사용자 기본 모델"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: EmailStr = Field(..., description="이메일")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "user123",
                "email": "user@example.com"
            }
        }
    )

class UserCreate(UserBase):
    """사용자 생성 모델"""
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "user123",
                "email": "user@example.com",
                "password": "password123"
            }
        }
    )

class UserUpdate(BaseModel):
    """사용자 수정 모델"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "newusername",
                "email": "new.email@example.com",
                "password": "newpassword123",
                "is_active": True
            }
        }
    )

class UserLogin(BaseModel):
    """사용자 로그인 모델"""
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., description="비밀번호")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }
    )

class UserResponse(UserBase):
    """사용자 응답 모델"""
    id: int = Field(..., description="사용자 ID")
    is_active: bool = Field(..., description="활성화 여부")
    created_at: datetime = Field(..., description="생성일시")
    hashed_password: Optional[str] = Field(None, description="해시된 비밀번호")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "user123",
                "email": "user@example.com",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00"
            }
        },
        exclude={"hashed_password"}  # 응답에서 비밀번호 제외
    )

class UsersResponse(BaseModel):
    """사용자 목록 응답 모델"""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [
                    {
                        "id": 1,
                        "username": "user1",
                        "email": "user1@example.com",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00"
                    },
                    {
                        "id": 2,
                        "username": "user2",
                        "email": "user2@example.com",
                        "is_active": True,
                        "created_at": "2024-01-01T00:00:00"
                    }
                ],
                "total": 2,
                "skip": 0,
                "limit": 10
            }
        }
    )

class User(BaseModel):
    """사용자 모델"""
    id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True) 