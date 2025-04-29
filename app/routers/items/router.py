from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field
from app.database.connection import get_db_connection
from app.utils.logger import log_query, setup_logger
import logging
from .queries import INSERT_ITEM, SELECT_ALL_ITEMS, SELECT_ITEM_BY_ID

# 로거 설정
logger = setup_logger("items")

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

class ItemCreate(BaseModel):
    """아이템 생성 요청 모델"""
    name: str = Field(..., min_length=1, max_length=100, description="아이템 이름")
    description: Optional[str] = Field(None, max_length=500, description="아이템 설명")
    price: float = Field(..., ge=0, description="아이템 가격")
    tax: Optional[float] = Field(None, ge=0, description="아이템 세금")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "새로운 아이템",
                "description": "아이템에 대한 설명입니다.",
                "price": 1000.0,
                "tax": 100.0
            }
        }

class ItemResponse(ItemCreate):
    """아이템 응답 모델"""
    id: int = Field(..., description="아이템 ID")

    class Config:
        from_attributes = True

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, db: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    새로운 아이템을 생성합니다.
    
    Args:
        item: 생성할 아이템 정보
        
    Returns:
        생성된 아이템 정보
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        # 요청 데이터 로깅
        logger.info(f"아이템 생성 요청: {item.model_dump()}")
        
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            item_data = item.model_dump()
            log_query(cursor, INSERT_ITEM, item_data)
            cursor.execute(INSERT_ITEM, item_data)
            result = cursor.fetchone()
            
            # 결과 데이터 로깅
            logger.info(f"생성된 아이템: {result}")
            
            db.commit()
            return result
    except Exception as e:
        db.rollback()
        logger.error(f"아이템 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=List[ItemResponse])
async def read_items(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    db: psycopg2.extensions.connection = Depends(get_db_connection)
):
    """
    모든 아이템 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        
    Returns:
        아이템 목록
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            params = {"skip": skip, "limit": limit}
            log_query(cursor, SELECT_ALL_ITEMS, params)
            cursor.execute(SELECT_ALL_ITEMS, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"아이템 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{item_id}", response_model=ItemResponse)
async def read_item(
    item_id: int = Path(..., ge=1, description="아이템 ID"),
    db: psycopg2.extensions.connection = Depends(get_db_connection)
):
    """
    특정 아이템을 조회합니다.
    
    Args:
        item_id: 조회할 아이템 ID
        
    Returns:
        아이템 정보
        
    Raises:
        HTTPException:
            - 404: 아이템을 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            params = {"item_id": item_id}
            log_query(cursor, SELECT_ITEM_BY_ID, params)
            cursor.execute(SELECT_ITEM_BY_ID, params)
            result = cursor.fetchone()
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item not found"
                )
            return result
    except Exception as e:
        logger.error(f"아이템 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 