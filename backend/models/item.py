"""
상품 기본 모델 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ItemImage(BaseModel):
    """상품 이미지 모델"""
    id: int = Field(..., description="이미지 ID")
    item_id: int = Field(..., description="상품 ID")
    image_path: str = Field(..., description="이미지 저장 디렉토리 경로")
    image_filename: str = Field(..., description="저장된 이미지 파일명")
    original_filename: str = Field(..., description="원본 파일명")
    file_extension: str = Field(..., description="파일 확장자")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    created_at: datetime = Field(..., description="생성일시")

    model_config = ConfigDict(from_attributes=True)

class ItemBase(BaseModel):
    """상품 기본 정보"""
    name: str = Field(..., min_length=1, max_length=100, description="상품 이름")
    description: Optional[str] = Field(None, description="상품 설명")
    price: float = Field(..., ge=0, description="상품 가격")
    tax: Optional[float] = Field(None, ge=0, description="상품 세금")

class ItemCreate(ItemBase):
    """상품 생성 요청 모델"""
    pass

class ItemUpdate(BaseModel):
    """상품 수정 요청 모델"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    tax: Optional[float] = Field(None, ge=0)

class ItemResponse(ItemBase):
    """상품 응답 모델"""
    id: int = Field(..., description="상품 ID")
    created_at: datetime = Field(..., description="생성일시")
    images: List[ItemImage] = Field(default_factory=list, description="상품 이미지 목록")

    model_config = ConfigDict(from_attributes=True) 