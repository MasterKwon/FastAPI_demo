"""
상품 리뷰 모델
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ItemReviewBase(BaseModel):
    """상품 리뷰 기본 모델"""
    item_id: int = Field(..., description="상품 ID")
    usr_id: int = Field(..., description="사용자 ID")
    review_content: str = Field(..., description="리뷰 내용")
    score: int = Field(..., ge=1, le=5, description="평점 (1-5)")

class ItemReviewCreate(ItemReviewBase):
    """상품 리뷰 생성 모델"""
    pass

class ItemReviewUpdate(BaseModel):
    """상품 리뷰 수정 모델"""
    review_content: str | None = Field(None, description="리뷰 내용")
    score: int | None = Field(None, ge=1, le=5, description="평점 (1-5)")

class ItemReviewInDB(ItemReviewBase):
    """DB의 상품 리뷰 모델"""
    id: int = Field(..., description="리뷰 ID")
    sentiment: str | None = Field(None, description="감성 분석 결과")
    confidence: int | None = Field(None, description="감성 분석 신뢰도 (%)")
    explanation: str | None = Field(None, description="감성 분석 설명")
    created_at: datetime = Field(..., description="생성일시")

    model_config = ConfigDict(from_attributes=True)

class ItemReview(ItemReviewInDB):
    """응답용 상품 리뷰 모델"""
    pass 