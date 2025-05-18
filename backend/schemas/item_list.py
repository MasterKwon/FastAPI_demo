"""
상품 목록 관련 스키마 정의
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from backend.schemas.item import ItemResponse

class ItemListResponse(BaseModel):
    """상품 목록 응답 모델"""
    items: List[ItemResponse] = Field(..., description="상품 목록")
    total: int = Field(..., description="전체 상품 수")
    skip: int = Field(..., description="건너뛴 레코드 수")
    limit: int = Field(..., description="반환된 레코드 수")

    class SortColumn(str, Enum):
        """정렬 기준 컬럼"""
        id = "id"
        name = "name"
        price = "price"
        created_at = "created_at"
        updated_at = "updated_at"

    class SortDirection(str, Enum):
        """정렬 방향"""
        asc = "asc"
        desc = "desc" 