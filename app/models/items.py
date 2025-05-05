"""
상품 관련 모델 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ItemSortColumn(str, Enum):
    """상품 정렬 컬럼"""
    id = "id"
    name = "name"
    price = "price"
    created_at = "created_at"

    model_config = ConfigDict(
        json_schema_extra={
            "example": "name"
        }
    )

class SortDirection(str, Enum):
    """정렬 방향"""
    asc = "ASC"
    desc = "DESC"

    model_config = ConfigDict(
        json_schema_extra={
            "example": "desc"
        }
    )

class ItemFilter(BaseModel):
    """상품 필터 모델"""
    name: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "스마트폰",
                "min_price": 500000,
                "max_price": 1500000,
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59"
            }
        }
    )

class ItemSort(BaseModel):
    """상품 정렬 모델"""
    column: ItemSortColumn
    direction: SortDirection

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "column": "price",
                "direction": "desc"
            }
        }
    )

class ItemBase(BaseModel):
    """상품 기본 정보"""
    name: str = Field(..., min_length=1, max_length=100, description="상품 이름")
    description: Optional[str] = Field(None, description="상품 설명")
    price: float = Field(..., ge=0, description="상품 가격")
    tax: Optional[float] = Field(None, ge=0, description="상품 세금")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "스마트폰",
                "description": "최신형 스마트폰",
                "price": 1000000,
                "tax": 100000
            }
        }
    )

class ItemCreate(ItemBase):
    """상품 생성 요청 모델"""
    pass

class ItemUpdate(BaseModel):
    """상품 수정 요청 모델"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    tax: Optional[float] = Field(None, ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "업데이트된 스마트폰",
                "description": "업데이트된 상품 설명",
                "price": 1200000,
                "tax": 120000
            }
        }
    )

class ItemImage(BaseModel):
    """상품 이미지 모델"""
    id: int = Field(..., description="이미지 ID")
    item_id: int = Field(..., description="상품 ID")
    image_path: str = Field(..., description="이미지 경로")
    image_filename: str = Field(..., description="이미지 파일명")
    original_filename: str = Field(..., description="원본 파일명")
    file_extension: str = Field(..., description="파일 확장자")
    file_size: int = Field(..., description="파일 크기")
    created_at: datetime = Field(..., description="생성일시")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "item_id": 1,
                "image_path": "/images/items/1",
                "image_filename": "smartphone.jpg",
                "original_filename": "my_smartphone.jpg",
                "file_extension": ".jpg",
                "file_size": 1024000,
                "created_at": "2024-01-01T00:00:00"
            }
        }
    )

class ItemResponse(ItemBase):
    """상품 응답 모델"""
    id: int = Field(..., description="상품 ID")
    created_at: datetime = Field(..., description="생성일시")
    images: List[ItemImage] = Field(default_factory=list, description="상품 이미지 목록")

    model_config = ConfigDict(
        json_schema_extra={
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
                        "image_path": "/images/items/1",
                        "image_filename": "smartphone.jpg",
                        "original_filename": "my_smartphone.jpg",
                        "file_extension": ".jpg",
                        "file_size": 1024000,
                        "created_at": "2024-01-01T00:00:00"
                    }
                ]
            }
        }
    )

class ItemsResponse(BaseModel):
    """상품 목록 응답 모델"""
    items: List[ItemResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name": "스마트폰",
                        "description": "최신형 스마트폰",
                        "price": 1000000,
                        "tax": 100000,
                        "created_at": "2024-01-01T00:00:00",
                        "images": []
                    },
                    {
                        "id": 2,
                        "name": "노트북",
                        "description": "고성능 노트북",
                        "price": 1500000,
                        "tax": 150000,
                        "created_at": "2024-01-02T00:00:00",
                        "images": []
                    }
                ],
                "total": 2,
                "skip": 0,
                "limit": 10
            }
        }
    ) 