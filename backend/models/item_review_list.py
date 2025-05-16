"""
상품 리뷰 목록 관련 모델 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .item_review import ItemReview

class ItemReviewSortColumn(str, Enum):
    """상품 리뷰 정렬 컬럼"""
    id = "id"
    score = "score"
    created_at = "created_at"
    confidence = "confidence"

class SortDirection(str, Enum):
    """정렬 방향"""
    asc = "ASC"
    desc = "DESC"

class ItemReviewFilter(BaseModel):
    """상품 리뷰 필터 모델"""
    item_id: Optional[int] = None
    usr_id: Optional[int] = None
    min_score: Optional[int] = Field(None, ge=1, le=5)
    max_score: Optional[int] = Field(None, ge=1, le=5)
    sentiment: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ItemReviewSort(BaseModel):
    """상품 리뷰 정렬 모델"""
    column: ItemReviewSortColumn
    direction: SortDirection

class ItemReviewsResponse(BaseModel):
    """상품 리뷰 목록 응답 모델"""
    item_reviews: List[ItemReview]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True) 