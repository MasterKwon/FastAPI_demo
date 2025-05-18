"""
상품 리뷰 목록 관련 스키마 정의
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

from backend.schemas.item_review import ReviewResponse

class ReviewListResponse(BaseModel):
    """리뷰 목록 응답 모델"""
    reviews: List[ReviewResponse] = Field(..., description="리뷰 목록")
    total: int = Field(..., description="전체 리뷰 수")
    skip: int = Field(..., description="건너뛴 레코드 수")
    limit: int = Field(..., description="반환된 레코드 수")

    class SortColumn(str, Enum):
        """정렬 기준 컬럼"""
        id = "id"
        rating = "rating"
        created_at = "created_at"
        updated_at = "updated_at"

    class SortDirection(str, Enum):
        """정렬 방향"""
        asc = "asc"
        desc = "desc" 