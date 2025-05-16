"""
사용자 목록 관련 모델 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .user import UserResponse

class UserSortColumn(str, Enum):
    """사용자 정렬 컬럼"""
    id = "id"
    username = "username"
    email = "email"
    created_at = "created_at"

class SortDirection(str, Enum):
    """정렬 방향"""
    asc = "ASC"
    desc = "DESC"

class UserFilter(BaseModel):
    """사용자 필터 모델"""
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class UserSort(BaseModel):
    """사용자 정렬 모델"""
    column: UserSortColumn
    direction: SortDirection

class UsersResponse(BaseModel):
    """사용자 목록 응답 모델"""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)

class FailedItem(BaseModel):
    """실패한 항목 모델"""
    item: dict
    error: str

class BulkUploadResponse(BaseModel):
    """대량 업로드 응답 모델"""
    success_count: int
    failed_count: int
    failed_items: List[FailedItem] 