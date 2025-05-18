"""
아이템 관련 라우터 모듈

이 모듈은 아이템 관련 API 엔드포인트를 제공합니다.
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, UploadFile, File
from typing import List, Optional, Dict, Any
import asyncpg
from backend.database.async_pool import get_async_db, async_db_pool
from backend.utils.logger import setup_logger, app_logger, LogType
from backend.database.exceptions import DatabaseError, ValidationError, BusinessLogicError
from backend.schemas.item import ItemCreate, ItemUpdate, ItemResponse, ItemsResponse
from backend.utils.decorators import log_operation
from backend.schemas.common import ResponseModel
from backend.queries.item_queries import (
    INSERT_ITEM, SELECT_ITEM_BY_ID, SELECT_ITEM_BY_NAME, SELECT_ITEMS_TEMPLATE,
    UPDATE_ITEM, DELETE_ITEM, BULK_INSERT_ITEMS
)
from datetime import datetime
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse
import logging

# 로거 설정
logger = setup_logger(__name__)

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ResponseModel[ItemResponse], status_code=status.HTTP_201_CREATED)
@log_operation(log_type=LogType.ALL)
async def create_item(item: ItemCreate):
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
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 아이템명 중복 체크
            existing_item = await async_db_pool.fetchrow(
                conn,
                SELECT_ITEM_BY_NAME,
                item.name
            )
            if existing_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 아이템명입니다."
                )
            
            # 아이템 생성
            row = await async_db_pool.fetchrow(
                conn,
                INSERT_ITEM,
                item.name,
                item.description,
                item.price,
                item.tax,
                datetime.utcnow()
            )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_ROUTER] 아이템 생성 완료: {item.name}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=ItemResponse(**dict(row)), message="Item created successfully", status_code=201)
            
    except DatabaseError as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 아이템 생성 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 예상치 못한 오류: {str(e)}",
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
    search: Optional[str] = None
):
    """
    모든 아이템 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        search: 검색어
        
    Returns:
        아이템 목록과 페이지네이션 정보
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 검색 조건이 있는 경우
            if search:
                where_condition = "WHERE name ILIKE $1 OR description ILIKE $1"
                query = SELECT_ITEMS_TEMPLATE.format(
                    where_condition=where_condition,
                    sort_column="created_at",
                    sort_direction="DESC"
                )
                rows = await async_db_pool.fetch(
                    conn,
                    query,
                    f"%{search}%",
                    limit,
                    skip
                )
            else:
                query = SELECT_ITEMS_TEMPLATE.format(
                    where_condition="",
                    sort_column="created_at",
                    sort_direction="DESC"
                )
                rows = await async_db_pool.fetch(
                    conn,
                    query,
                    limit,
                    skip
                )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_ROUTER] 아이템 목록 조회 완료: {len(rows)}개",
                log_type=LogType.ALL
            )
            
            return ResponseModel(
                data=ItemsResponse(
                    items=[ItemResponse(**dict(row)) for row in rows],
                    total=len(rows),
                    skip=skip,
                    limit=limit
                ),
                message="Items retrieved successfully"
            )
            
    except DatabaseError as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 아이템 목록 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 예상치 못한 오류: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{item_id}", response_model=ResponseModel[ItemResponse])
@log_operation(log_type=LogType.ALL)
async def read_item(item_id: int = Path(..., ge=1, description="아이템 ID")):
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
        pool = get_async_db()
        async with pool.acquire() as conn:
            row = await async_db_pool.fetchrow(
                conn,
                SELECT_ITEM_BY_ID,
                item_id
            )
            
            if not row:
                app_logger.log(
                    logging.WARNING,
                    f"[ITEM_ROUTER] 아이템을 찾을 수 없음: {item_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item not found"
                )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_ROUTER] 아이템 상세 조회 완료: {item_id}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=ItemResponse(**dict(row)), message="Item retrieved successfully")
            
    except DatabaseError as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 아이템 상세 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 예상치 못한 오류: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{item_id}", response_model=ResponseModel[ItemResponse])
@log_operation(log_type=LogType.ALL)
async def update_item(
    item_id: int = Path(..., ge=1, description="아이템 ID"),
    item: ItemUpdate = None
):
    """
    아이템 정보를 수정합니다.
    
    Args:
        item_id: 수정할 아이템 ID
        item: 수정할 아이템 정보
        
    Returns:
        수정된 아이템 정보
        
    Raises:
        HTTPException:
            - 404: 아이템을 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 아이템 존재 확인
            exists = await async_db_pool.fetchrow(
                conn,
                "SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)",
                item_id
            )
            
            if not exists:
                app_logger.log(
                    logging.WARNING,
                    f"[ITEM_ROUTER] 아이템을 찾을 수 없음: {item_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item not found"
                )
            
            # 아이템 수정
            row = await async_db_pool.fetchrow(
                conn,
                UPDATE_ITEM,
                item_id,
                item.name,
                item.description,
                item.price,
                item.tax
            )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_ROUTER] 아이템 수정 완료: {item_id}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=ItemResponse(**dict(row)), message="Item updated successfully")
            
    except DatabaseError as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 아이템 수정 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 예상치 못한 오류: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{item_id}", response_model=ResponseModel)
@log_operation(log_type=LogType.ALL)
async def delete_item(item_id: int = Path(..., ge=1, description="아이템 ID")):
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
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 아이템 존재 확인
            exists = await async_db_pool.fetchrow(
                conn,
                "SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)",
                item_id
            )
            
            if not exists:
                app_logger.log(
                    logging.WARNING,
                    f"[ITEM_ROUTER] 아이템을 찾을 수 없음: {item_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item not found"
                )
            
            # 아이템 삭제
            await async_db_pool.execute_query(
                conn,
                DELETE_ITEM,
                item_id
            )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_ROUTER] 아이템 삭제 완료: {item_id}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(message="Item deleted successfully")
            
    except DatabaseError as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 아이템 삭제 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 예상치 못한 오류: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/bulk-upload", response_model=ResponseModel[Dict[str, Any]])
@log_operation(log_type=LogType.ALL)
async def bulk_upload_items(file: UploadFile = File(...)):
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
        
        # 데이터 검증 및 변환
        success_count = 0
        error_count = 0
        errors = []
        
        pool = get_async_db()
        async with pool.acquire() as conn:
            async with async_db_pool.transaction(conn):
                for index, row in df.itertuples():
                    try:
                        # 아이템 생성 (컬럼 순서 기반 처리)
                        await async_db_pool.execute_query(
                            conn,
                            INSERT_ITEM,
                            row[1],  # name (첫 번째 컬럼)
                            row[2],  # description (두 번째 컬럼)
                            float(row[3]),  # price (세 번째 컬럼)
                            float(row[4] if len(row) > 4 else 0),  # tax (네 번째 컬럼)
                            datetime.utcnow()
                        )
                        
                        success_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {index + 2}: {str(e)}")
                        error_count += 1
        
        app_logger.log(
            logging.INFO,
            f"[ITEM_ROUTER] 대량 업로드 완료: 성공 {success_count}개, 실패 {error_count}개",
            log_type=LogType.ALL
        )
        
        return ResponseModel(
            data={
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors
            },
            message="Bulk upload completed"
        )
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 대량 업로드 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/download-template")
@log_operation(log_type=LogType.ALL)
async def download_template():
    """
    아이템 대량 등록을 위한 엑셀 템플릿을 다운로드합니다.
    
    Returns:
        엑셀 템플릿 파일
        
    Raises:
        HTTPException: 500 - 파일 생성 실패 시
    """
    try:
        # 템플릿 데이터 생성 (컬럼 순서 기반)
        data = [
            ['아이템명1', '아이템 설명1', 1000, 100],  # 첫 번째 행
            ['아이템명2', '아이템 설명2', 2000, 200]   # 두 번째 행
        ]
        df = pd.DataFrame(data, columns=['name', 'description', 'price', 'tax'])
        
        # 엑셀 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Template')
            
            # 워크시트 가져오기
            worksheet = writer.sheets['Template']
            
            # 컬럼 너비 조정
            worksheet.set_column('A:A', 20)  # name
            worksheet.set_column('B:B', 40)  # description
            worksheet.set_column('C:C', 15)  # price
            worksheet.set_column('D:D', 15)  # tax
        
        output.seek(0)
        
        app_logger.log(
            logging.INFO,
            "[ITEM_ROUTER] 템플릿 다운로드 완료",
            log_type=LogType.ALL
        )
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                'Content-Disposition': 'attachment; filename=item_template.xlsx'
            }
        )
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_ROUTER] 템플릿 다운로드 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 