"""
사용자 관련 스키마 정의
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from backend.schemas.base import TimeStampModel

class UserBase(BaseModel):
    """사용자 기본 모델"""
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: EmailStr = Field(..., description="이메일")
    is_active: bool = Field(True, description="활성화 여부")

class UserCreate(UserBase):
    """사용자 생성 모델"""
    password: str = Field(..., min_length=8, description="비밀번호")

class UserUpdate(BaseModel):
    """사용자 수정 모델"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="사용자명")
    email: Optional[EmailStr] = Field(None, description="이메일")
    password: Optional[str] = Field(None, min_length=8, description="비밀번호")
    is_active: Optional[bool] = Field(None, description="활성화 여부")

class UserResponse(UserBase, TimeStampModel):
    """사용자 응답 모델"""
    id: int = Field(..., description="사용자 ID")

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    """사용자 로그인 모델"""
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., min_length=8, description="비밀번호") 