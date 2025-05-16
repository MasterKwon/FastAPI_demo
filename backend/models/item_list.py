"""
상품 목록 관련 모델 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum
from .item import ItemResponse

class ItemSortColumn(str, Enum):
    """상품 정렬 컬럼"""
    id = "id"
    name = "name"
    price = "price"
    created_at = "created_at"

class SortDirection(str, Enum):
    """정렬 방향"""
    asc = "ASC"
    desc = "DESC"

class ItemFilter(BaseModel):
    """상품 필터 모델"""
    name: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ItemSort(BaseModel):
    """상품 정렬 모델"""
    column: ItemSortColumn
    direction: SortDirection

class ItemsResponse(BaseModel):
    """상품 목록 응답 모델"""
    items: List[ItemResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True) 