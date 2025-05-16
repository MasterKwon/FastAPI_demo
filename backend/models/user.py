"""
사용자 기본 모델 정의
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """사용자 기본 모델"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: EmailStr = Field(..., description="이메일")

class UserCreate(UserBase):
    """사용자 생성 모델"""
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")

class UserUpdate(BaseModel):
    """사용자 수정 모델"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    """사용자 로그인 모델"""
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., description="비밀번호")

class UserResponse(UserBase):
    """사용자 응답 모델"""
    id: int = Field(..., description="사용자 ID")
    is_active: bool = Field(..., description="활성화 여부")
    created_at: datetime = Field(..., description="생성일시")
    hashed_password: Optional[str] = Field(None, description="해시된 비밀번호")

    model_config = ConfigDict(
        from_attributes=True,
        exclude={"hashed_password"}  # 응답에서 비밀번호 제외
    ) 