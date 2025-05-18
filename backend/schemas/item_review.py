"""
상품 리뷰 관련 스키마 정의
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from backend.schemas.base import TimeStampModel

class ItemReviewSortColumn(str, Enum):
    """리뷰 정렬 기준 컬럼"""
    created_at = "created_at"
    rating = "rating"
    sentiment = "sentiment"
    confidence = "confidence"

class ReviewBase(BaseModel):
    """리뷰 기본 모델"""
    content: str = Field(..., min_length=1, max_length=1000, description="리뷰 내용")
    rating: int = Field(..., ge=1, le=5, description="평점 (1-5)")
    is_active: bool = Field(True, description="활성화 여부")

class ReviewCreate(ReviewBase):
    """리뷰 생성 모델"""
    item_id: int = Field(..., description="상품 ID")

class ReviewUpdate(BaseModel):
    """리뷰 수정 모델"""
    content: Optional[str] = Field(None, min_length=1, max_length=1000, description="리뷰 내용")
    rating: Optional[int] = Field(None, ge=1, le=5, description="평점 (1-5)")
    is_active: Optional[bool] = Field(None, description="활성화 여부")

class ReviewInDB(ReviewBase, TimeStampModel):
    """DB에 저장된 리뷰 모델"""
    id: int = Field(..., description="리뷰 ID")
    user_id: int = Field(..., description="사용자 ID")
    item_id: int = Field(..., description="상품 ID")
    sentiment: Optional[str] = Field(None, description="감성 분석 결과")
    confidence: Optional[int] = Field(None, description="감성 분석 신뢰도 (%)")
    explanation: Optional[str] = Field(None, description="감성 분석 설명")

class ReviewResponse(ReviewBase, TimeStampModel):
    """리뷰 응답 모델"""
    id: int = Field(..., description="리뷰 ID")
    user_id: int = Field(..., description="사용자 ID")
    item_id: int = Field(..., description="상품 ID")
    sentiment: Optional[str] = Field(None, description="감성 분석 결과")
    confidence: Optional[int] = Field(None, description="감성 분석 신뢰도 (%)")
    explanation: Optional[str] = Field(None, description="감성 분석 설명")

    model_config = ConfigDict(from_attributes=True) 