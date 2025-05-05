"""
상품 모델
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ItemImage(BaseModel):
    id: int = Field(..., description="이미지 ID")
    item_id: int = Field(..., description="상품 ID")
    image_path: str = Field(..., description="이미지 저장 디렉토리 경로")
    image_filename: str = Field(..., description="저장된 이미지 파일명")
    original_filename: str = Field(..., description="원본 파일명")
    file_extension: str = Field(..., description="파일 확장자")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    created_at: datetime = Field(..., description="생성일시")

    json_schema_extra = {
        "example": {
            "id": 1,
            "item_id": 1,
            "image_path": "app/upload/images",
            "image_filename": "550e8400-e29b-41d4-a716-446655440000_1234567890.jpg",
            "original_filename": "smartphone.jpg",
            "file_extension": ".jpg",
            "file_size": 1024000,
            "created_at": "2024-01-01T00:00:00"
        }
    }

class ItemBase(BaseModel):
    """아이템 기본 모델"""
    name: str = Field(..., description="상품명")
    description: Optional[str] = Field(None, description="상품 설명")
    price: float = Field(..., ge=0, description="가격")
    tax: Optional[float] = Field(None, ge=0, description="세금")

    json_schema_extra = {
        "example": {
            "name": "스마트폰",
            "description": "최신형 스마트폰",
            "price": 1000000,
            "tax": 100000
        }
    }

class ItemCreate(ItemBase):
    """아이템 생성 모델"""
    name: str = Field(..., min_length=1, max_length=100, description="상품명")
    description: Optional[str] = Field(None, max_length=500, description="상품설명")
    price: float = Field(..., ge=0, description="상품가격")
    tax: Optional[float] = Field(None, ge=0, description="세금")

    json_schema_extra = {
        "example": {
            "name": "스마트폰",
            "description": "최신형 스마트폰",
            "price": 1000000,
            "tax": 100000
        }
    }

class ItemUpdate(ItemBase):
    """아이템 수정 모델"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    tax: Optional[float] = None

    json_schema_extra = {
        "example": {
            "name": "스마트폰 Pro",
            "description": "업그레이드된 최신형 스마트폰",
            "price": 1200000,
            "tax": 120000
        }
    }

class Item(ItemBase):
    id: int = Field(..., description="상품 ID")
    created_at: datetime = Field(..., description="생성일시")
    images: List[ItemImage] = Field(default_factory=list, description="상품 이미지 목록")

    class Config:
        from_attributes = True

class ItemResponse(ItemBase):
    """아이템 응답 모델"""
    id: int = Field(..., description="상품 ID")
    created_at: datetime = Field(..., description="생성일시")
    images: List[ItemImage] = Field(default_factory=list, description="상품 이미지 목록")

    json_schema_extra = {
        "example": {
            "id": 1,
            "name": "스마트폰",
            "description": "최신형 스마트폰",
            "price": 1000000,
            "tax": 100000,
            "created_at": "2024-01-01T00:00:00",
            "images": [
                {
                    "id": 1,
                    "item_id": 1,
                    "image_path": "app/upload/images",
                    "image_filename": "550e8400-e29b-41d4-a716-446655440000_1234567890.jpg",
                    "original_filename": "smartphone.jpg",
                    "file_extension": ".jpg",
                    "file_size": 1024000,
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
        }
    } 