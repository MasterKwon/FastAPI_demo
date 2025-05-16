"""
아이템 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, UploadFile, File
from typing import List, Optional
import asyncpg
from backend.database.async_pool import get_async_db
from backend.utils.logger import log_query, setup_logger, app_logger, LogType
from backend.database.exceptions import handle_database_error
from backend.queries.item_queries import (
    INSERT_ITEM, SELECT_ITEM_BY_ID, SELECT_ITEMS_TEMPLATE,
    UPDATE_ITEM, DELETE_ITEM, SELECT_ITEM_COUNT
)
from backend.models.items import (
    ItemCreate, ItemResponse, ItemUpdate, ItemsResponse,
    ItemSortColumn, SortDirection, BulkUploadResponse
)
from enum import Enum
import logging
from datetime import datetime
import pandas as pd
import os
import time
import re
from backend.utils.decorators import log_operation
from backend.schemas.common import ResponseModel
from backend.services.item_service import ItemService
from io import BytesIO

# 로거 설정
logger = setup_logger(__name__)

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ResponseModel[ItemResponse], status_code=status.HTTP_201_CREATED)
@log_operation(log_type=LogType.ALL)
async def create_item(
    item: ItemCreate,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    새로운 아이템을 생성합니다.
    
    Args:
        item: 생성할 아이템 정보
        
    Returns:
        생성된 아이템 정보
        
    Raises:
        HTTPException: 
            - 400: 아이템명이 이미 등록된 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 아이템명 중복 체크
        existing_item = await db.fetchrow(
            SELECT_ITEM_BY_ID,
            item.name
        )
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 아이템명입니다."
            )
        
        # 아이템 정보 저장
        result = await db.fetchrow(
            INSERT_ITEM,
            item.name,
            item.description,
            item.price,
            datetime.now()
        )
        
        app_logger.log(
            logging.INFO,
            f"아이템 생성 성공: {result['id']}",
            log_type=LogType.ALL
        )
        
        return ResponseModel(data=result, message="Item created successfully", status_code=201)
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"아이템 생성 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=ResponseModel[ItemsResponse])
@log_operation(log_type=LogType.ALL)
async def read_items(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    모든 아이템 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        sort_by: 정렬 기준 컬럼 (기본값: created_at)
        sort_direction: 정렬 방향 (기본값: desc)
        
    Returns:
        아이템 목록과 페이지네이션 정보
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        # 아이템 목록 조회
        query = SELECT_ITEMS_TEMPLATE.format(
            where_condition="",
            sort_column=sort_by,
            sort_direction=sort_direction
        )
        items = await db.fetch(query, limit, skip)
        
        # 첫 번째 레코드에서 total_count 추출
        total = items[0]["total_count"] if items else 0
        
        # total_count 필드 제거
        for item in items:
            item.pop("total_count", None)
        
        return ResponseModel(data={
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit
        }, message="Items retrieved successfully")
        
    except Exception as e:
        logger.error(f"아이템 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )

@router.get("/{item_id}", response_model=ResponseModel[ItemResponse])
@log_operation(log_type=LogType.ALL)
async def read_item(
    item_id: int = Path(..., ge=1, description="아이템 ID"),
    db: asyncpg.Connection = Depends(get_async_db)
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
        item = await db.fetchrow(
            SELECT_ITEM_BY_ID,
            item_id
        )
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        return ResponseModel(data=item, message="Item retrieved successfully")
        
    except Exception as e:
        logger.error(f"아이템 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/search/", response_model=ResponseModel[List[ItemResponse]])
@log_operation(log_type=LogType.ALL)
async def search_items(
    name: Optional[str] = None,
    description: Optional[str] = None,
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    아이템을 검색합니다.
    
    Args:
        name: 검색할 아이템명 (선택)
        description: 검색할 설명 (선택)
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        sort_by: 정렬 기준 컬럼 (기본값: created_at)
        sort_direction: 정렬 방향 (기본값: desc)
        
    Returns:
        검색된 아이템 목록
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        # 검색 조건 구성
        conditions = []
        if name:
            conditions.append(f"name ILIKE '%{name}%'")
        if description:
            conditions.append(f"description ILIKE '%{description}%'")
        
        where_condition = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # 아이템 검색
        query = SELECT_ITEMS_TEMPLATE.format(
            where_condition=where_condition,
            sort_column=sort_by,
            sort_direction=sort_direction
        )
        items = await db.fetch(query, limit, skip)
        
        # total_count 필드 제거
        for item in items:
            item.pop("total_count", None)
        
        return ResponseModel(data=items, message="Items retrieved successfully")
        
    except Exception as e:
        logger.error(f"아이템 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )

@router.put("/{item_id}", response_model=ResponseModel[ItemResponse])
@log_operation(log_type=LogType.ALL)
async def update_item(
    item_id: int,
    item: ItemUpdate,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    아이템 정보를 업데이트합니다.
    
    Args:
        item_id: 업데이트할 아이템 ID
        item: 업데이트할 아이템 정보
        
    Returns:
        업데이트된 아이템 정보
        
    Raises:
        HTTPException:
            - 404: 아이템을 찾을 수 없는 경우
            - 400: 아이템명이 이미 등록된 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 아이템 존재 여부 확인
        existing_item = await db.fetchrow(
            SELECT_ITEM_BY_ID,
            item_id
        )
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # 아이템명 중복 체크
        if item.name and item.name != existing_item["name"]:
            name_exists = await db.fetchrow(
                SELECT_ITEM_BY_ID,
                item.name
            )
            if name_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 아이템명입니다."
                )
        
        # 아이템 정보 업데이트
        result = await db.fetchrow(
            UPDATE_ITEM,
            item_id,
            item.name,
            item.description,
            item.price
        )
        
        return ResponseModel(data=result, message="Item updated successfully")
        
    except Exception as e:
        logger.error(f"아이템 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )

@router.delete("/{item_id}", response_model=ResponseModel)
@log_operation(log_type=LogType.ALL)
async def delete_item(
    item_id: int,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    아이템을 삭제합니다.
    
    Args:
        item_id: 삭제할 아이템 ID
        
    Returns:
        삭제 결과
        
    Raises:
        HTTPException:
            - 404: 아이템을 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 아이템 존재 여부 확인
        existing_item = await db.fetchrow(
            SELECT_ITEM_BY_ID,
            item_id
        )
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found"
            )
        
        # 아이템 삭제
        await db.execute(
            DELETE_ITEM,
            item_id
        )
        
        return ResponseModel(message="Item deleted successfully")
        
    except Exception as e:
        logger.error(f"아이템 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/bulk-upload", response_model=ResponseModel[BulkUploadResponse])
@log_operation(log_type=LogType.ALL)
async def bulk_upload_items(
    file: UploadFile = File(...),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    엑셀 파일을 통해 아이템을 대량 등록합니다.
    
    Args:
        file: 업로드할 엑셀 파일
        
    Returns:
        대량 등록 결과
        
    Raises:
        HTTPException:
            - 400: 파일 형식이 잘못된 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 파일 확장자 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Excel files are allowed"
            )
        
        # 파일 읽기
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # 필수 컬럼 검증
        required_columns = ['name', 'description', 'price']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Excel file must contain these columns: {', '.join(required_columns)}"
            )
        
        # 데이터 검증 및 변환
        success_count = 0
        error_count = 0
        errors = []
        
        async with db.transaction():
            for index, row in df.iterrows():
                try:
                    # 아이템명 중복 체크
                    name_exists = await db.fetchrow(
                        SELECT_ITEM_BY_ID,
                        row['name']
                    )
                    if name_exists:
                        errors.append(f"Row {index + 2}: Item name already exists")
                        error_count += 1
                        continue
                    
                    # 아이템 생성
                    await db.execute(
                        INSERT_ITEM,
                        row['name'],
                        row['description'],
                        row['price'],
                        datetime.now()
                    )
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    error_count += 1
        
        return ResponseModel(data={
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }, message="Bulk upload completed")
        
    except Exception as e:
        logger.error(f"대량 업로드 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    ) 