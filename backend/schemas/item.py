"""
아이템 관련 스키마 모듈

이 모듈은 아이템 관련 Pydantic 모델을 정의합니다.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class ItemBase(BaseModel):
    """아이템 기본 모델"""
    name: str = Field(..., min_length=1, max_length=100, description="아이템명")
    description: Optional[str] = Field(None, description="아이템 설명")
    price: Decimal = Field(..., ge=0, description="아이템 가격")
    tax: Optional[Decimal] = Field(0, ge=0, description="아이템 세금")

    @validator('price')
    def validate_price(cls, v):
        """가격 유효성 검사"""
        if v < 0:
            raise ValueError("가격은 0 이상이어야 합니다.")
        return v

    @validator('tax')
    def validate_tax(cls, v):
        """세금 유효성 검사"""
        if v < 0:
            raise ValueError("세금은 0 이상이어야 합니다.")
        return v

class ItemCreate(ItemBase):
    """아이템 생성 모델"""
    pass

class ItemUpdate(BaseModel):
    """아이템 수정 모델"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="아이템명")
    description: Optional[str] = Field(None, description="아이템 설명")
    price: Optional[Decimal] = Field(None, ge=0, description="아이템 가격")
    tax: Optional[Decimal] = Field(None, ge=0, description="아이템 세금")

class ItemResponse(ItemBase):
    """아이템 응답 모델"""
    id: int = Field(..., description="아이템 ID")
    created_at: datetime = Field(..., description="생성일시")

    class Config:
        """Pydantic 설정"""
        from_attributes = True

class ItemsResponse(BaseModel):
    """아이템 목록 응답 모델"""
    items: List[ItemResponse] = Field(..., description="아이템 목록")
    total: int = Field(..., description="전체 아이템 수")
    skip: int = Field(..., description="건너뛴 레코드 수")
    limit: int = Field(..., description="반환된 레코드 수") 