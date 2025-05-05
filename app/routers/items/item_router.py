"""
상품 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, UploadFile, File
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from io import BytesIO
from app.database.pool import get_db
from app.utils.logger import logger, app_logger, log_operation, log_query, LogType
from app.services.bulk_upload import validate_excel_data, ExcelValidationError
from .item_queries import (
    INSERT_ITEM, SELECT_ALL_ITEMS, SELECT_ITEM_BY_ID, BULK_INSERT_ITEMS,
    UPDATE_ITEM, DELETE_ITEM, ImageQueries, SELECT_ITEM_COUNT, SEARCH_ITEMS_TEMPLATE
)
from app.database.schemas import CREATE_ALL_TABLES
from app.models.item import ItemCreate, ItemResponse, ItemImage
import time
import logging
from enum import Enum
from fastapi.responses import StreamingResponse
from app.utils.file_handler import save_file, delete_file, FileType
import os
from datetime import datetime

router = APIRouter(
    prefix="/items",
    tags=["items"]
)

# 정렬 가능한 컬럼 정의
class ItemSortColumn(str, Enum):
    id = "id"
    name = "name"
    price = "price"
    created_at = "created_at"

# 정렬 방향 정의
class SortDirection(str, Enum):
    asc = "ASC"
    desc = "DESC"

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
@log_operation(log_type=LogType.ALL)
async def create_item(
    item: ItemCreate,
    image: Optional[UploadFile] = File(None),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    새로운 상품을 생성합니다.
    """
    try:
        cursor = db.cursor()
        
        # 상품 정보 저장
        cursor.execute(
            INSERT_ITEM,
            {
                "name": item.name,
                "description": item.description,
                "price": item.price,
                "tax": item.tax,
                "created_at": datetime.now()
            }
        )
        result = cursor.fetchone()
        
        # 이미지가 있는 경우 저장
        item_image = None
        if image:
            # add_item_image 함수를 재사용하여 이미지 저장
            item_image = await add_item_image(
                item_id=result["id"],
                image=image,
                db=db
            )
        
        db.commit()
        
        # 응답 객체 생성
        response = ItemResponse(
            id=result["id"],
            name=item.name,
            description=item.description,
            price=item.price,
            tax=item.tax,
            created_at=result["created_at"],
            images=[item_image] if item_image else []
        )
        
        app_logger.log(
            logging.INFO,
            f"상품 생성 성공: {result['id']}",
            log_type=LogType.ALL
        )
        
        return response
        
    except Exception as e:
        db.rollback()
        app_logger.log(
            logging.ERROR,
            f"상품 생성 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ItemResponse])
@log_operation(log_type=LogType.ALL)
async def get_items(
    name: Optional[str] = None,
    description: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=10000, description="반환할 최대 레코드 수 (최대 10000)"),
    sort_by: Optional[ItemSortColumn] = Query(
        None,
        description="정렬 기준 컬럼 (미지정시 created_at)"
    ),
    sort_order: Optional[SortDirection] = Query(
        None,
        description="정렬 방향 (미지정시 DESC)"
    ),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    상품 목록을 조회합니다. 검색 조건이 없으면 전체 목록을 반환합니다.
    
    Args:
        name: 상품명 검색 (부분 일치)
        description: 상품 설명 검색 (부분 일치)
        min_price: 최소 가격
        max_price: 최대 가격
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수 (최대 10000)
        sort_by: 정렬 기준 컬럼
        sort_order: 정렬 방향
    """
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            # 정렬 컬럼과 방향 결정
            sort_column = (
                sort_by.value 
                if sort_by and sort_by in ItemSortColumn.__members__.values()
                else "created_at"
            )
            
            sort_direction = (
                sort_order.value
                if sort_order and sort_order in SortDirection.__members__.values()
                else "DESC"
            )

            # 동적 쿼리 생성
            where_clauses = []
            params = {"limit": limit, "offset": skip}
            
            if name is not None:
                where_clauses.append("i.name LIKE %(name)s")
                params["name"] = f"%{name}%"
            
            if description is not None:
                where_clauses.append("i.description LIKE %(description)s")
                params["description"] = f"%{description}%"
            
            if min_price is not None:
                where_clauses.append("i.price >= %(min_price)s")
                params["min_price"] = min_price
            
            if max_price is not None:
                where_clauses.append("i.price <= %(max_price)s")
                params["max_price"] = max_price
            
            # WHERE 절 구성
            where_condition = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            # 전체 상품 수 조회
            count_query = f"SELECT COUNT(*) FROM items i {where_condition}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()["count"]
            
            # 상품 목록 조회
            query = SEARCH_ITEMS_TEMPLATE.format(
                where_condition=where_condition,
                sort_column=sort_column,
                sort_direction=sort_direction
            )
            cursor.execute(query, params)
            items = cursor.fetchall()
            
            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"상품 목록 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/download-excel")
@log_operation(log_type=LogType.ALL)
async def download_items_excel(
    name: Optional[str] = None,
    description: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=10000, description="반환할 최대 레코드 수"),
    sort_by: Optional[ItemSortColumn] = Query(
        None,
        description="정렬 기준 컬럼 (미지정시 created_at)"
    ),
    sort_order: Optional[SortDirection] = Query(
        None,
        description="정렬 방향 (미지정시 DESC)"
    ),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    상품 목록을 엑셀 파일로 다운로드합니다. 검색 조건이 없으면 전체 목록을 다운로드합니다.
    
    Args:
        name: 상품명 검색 (부분 일치)
        description: 상품 설명 검색 (부분 일치)
        min_price: 최소 가격
        max_price: 최대 가격
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수 (최대 10000)
        sort_by: 정렬 기준 컬럼
        sort_order: 정렬 방향
    """
    try:
        # 아이템 목록 조회
        items = await get_items(
            name=name,
            description=description,
            min_price=min_price,
            max_price=max_price,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            db=db
        )
        
        if not items["items"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="다운로드할 데이터가 없습니다."
            )
        
        # DataFrame 생성
        df = pd.DataFrame(items["items"])
        
        # datetime 컬럼의 시간대 정보 제거
        if 'created_at' in df.columns:
            df['created_at'] = df['created_at'].dt.tz_localize(None)
        
        # 컬럼 순서 및 이름 설정
        df = df[['id', 'name', 'description', 'price', 'tax', 'created_at']]
        df.columns = ['ID', '상품명', '상품설명', '가격', '세금', '생성일시']
        
        # 엑셀 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='상품 목록')
            
            # 엑셀 스타일 설정
            workbook = writer.book
            worksheet = writer.sheets['상품 목록']
            
            # 컬럼 너비 자동 조정
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet.set_column(idx, idx, max_length + 2)
        
        output.seek(0)
        
        # 파일명 생성
        filename = f"items_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"엑셀 다운로드 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/bulk-upload", response_model=dict)
@log_operation(log_type=LogType.ALL)
async def bulk_upload_items(
    file: UploadFile = File(...),
    all_or_nothing: bool = Query(
        default=False,
        description="True: 전체 성공 또는 전체 실패 (벌크 인서트), False: 부분 성공 허용 (개별 인서트)"
    ),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    엑셀 파일을 통해 아이템을 대량으로 등록합니다.
    컬럼 순서: 상품명, 상품설명, 가격, 세금
    
    Args:
        file: 엑셀 파일
        all_or_nothing: True인 경우 전체 성공 또는 전체 실패, False인 경우 부분 성공 허용
    """
    # 시간 측정 변수들을 미리 초기화
    start_time = time.time()
    file_reading_time = 0
    validation_time = 0
    db_operation_time = 0
    
    try:
        # 기존 방식의 로깅
        logger.info(f"파일 업로드 시작: {file.filename}")
        
        # 새로운 방식의 선택적 로깅
        app_logger.log(
            logging.INFO,
            f"파일 처리 시작: {file.filename}",
            log_type=LogType.ALL
        )
        
        # 파일 확장자 검증 및 엑셀 파일 읽기
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="엑셀 파일(.xlsx 또는 .xls)만 업로드 가능합니다."
            )
        
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), header=0)
        
        file_reading_time = time.time() - start_time
        logger.info(f"파일 읽기 소요 시간: {file_reading_time:.2f}초")
        
        # 데이터 검증 시작
        validation_start = time.time()
        
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="엑셀 파일에 데이터가 없습니다."
            )
        
        # 필요한 컬럼 수 확인
        if len(df.columns) < 3:  # 최소 상품명, 상품설명, 가격은 필요
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="필수 컬럼이 부족합니다. 상품명, 상품설명, 가격 순서로 입력해주세요."
            )
        
        # 데이터 검증 및 변환
        valid_items = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # 인덱스로 데이터 접근
                name = str(row.iloc[0]).strip()  # 상품명
                description = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else None  # 상품설명
                
                # 가격 검증
                try:
                    price = float(row.iloc[2])  # 가격
                    if price < 0:
                        raise ValueError("가격은 0 이상이어야 합니다")
                except (ValueError, TypeError):
                    errors.append({
                        "row": idx + 2,
                        "error": "가격은 숫자여야 하며, 0 이상이어야 합니다"
                    })
                    continue
                
                # 세금 검증 (선택적)
                tax = None
                if len(row) > 3 and not pd.isna(row.iloc[3]):
                    try:
                        tax = float(row.iloc[3])  # 세금
                        if tax < 0:
                            raise ValueError("세금은 0 이상이어야 합니다")
                    except (ValueError, TypeError):
                        errors.append({
                            "row": idx + 2,
                            "error": "세금은 숫자여야 하며, 0 이상이어야 합니다"
                        })
                        continue
                
                # 상품명 필수 체크
                if pd.isna(name) or name.strip() == "":
                    errors.append({
                        "row": idx + 2,
                        "error": "상품명은 필수입니다"
                    })
                    continue
                
                item = ItemCreate(
                    name=name,
                    description=description,
                    price=price,
                    tax=tax
                )
                valid_items.append(item)
                
            except Exception as e:
                # logger.error(f"행 {idx + 2} 처리 중 오류: {str(e)}")
                errors.append({
                    "row": idx + 2,
                    "error": str(e)
                })
        
        if not valid_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "유효한 데이터가 없습니다.",
                    "errors": errors
                }
            )
        
        validation_time = time.time() - validation_start
        logger.info(f"데이터 검증 소요 시간: {validation_time:.2f}초")
        
        # 데이터베이스 저장
        success_count = 0
        failed_items = []
        BATCH_SIZE = 500
        
        # DB 저장 시작
        db_operation_start = time.time()
        
        if all_or_nothing:
            try:
                with db.cursor(cursor_factory=RealDictCursor) as cursor:
                    # 벌크 인서트용 데이터 준비
                    names = [item.name for item in valid_items]
                    descriptions = [item.description for item in valid_items]
                    prices = [item.price for item in valid_items]
                    taxes = [item.tax if item.tax is not None else None for item in valid_items]
                    
                    # 벌크 인서트 실행
                    cursor.execute(BULK_INSERT_ITEMS, {
                        'names': names,
                        'descriptions': descriptions,
                        'prices': prices,
                        'taxes': taxes
                    })
                    
                    success_count = len(valid_items)
                    db.commit()
                    
            except Exception as e:
                db.rollback()
                for item in valid_items:
                    failed_items.append({
                        "name": item.name,
                        "error": str(e)
                    })
        else:
            with db.cursor(cursor_factory=RealDictCursor) as cursor:
                batch_count = 0
                
                for idx, item in enumerate(valid_items, 1):
                    try:
                        item_data = {
                            "name": item.name,
                            "description": item.description,
                            "price": item.price,
                            "tax": item.tax
                        }
                        cursor.execute(INSERT_ITEM, item_data)
                        success_count += 1
                        batch_count += 1
                        
                        # 배치 크기에 도달하거나 마지막 아이템인 경우 커밋
                        if batch_count >= BATCH_SIZE or idx == len(valid_items):
                            db.commit()
                            logger.info(f"배치 커밋 완료: {success_count}/{len(valid_items)} 건 처리됨")
                            batch_count = 0
                            
                    except Exception as e:
                        failed_items.append({
                            "name": item.name,
                            "error": str(e)
                        })
                        
                        # 에러 발생 시에도 배치 크기에 도달했거나 마지막 아이템이면 커밋
                        if batch_count >= BATCH_SIZE or idx == len(valid_items):
                            db.commit()
                            logger.info(f"배치 커밋 완료 (에러 포함): {success_count}/{len(valid_items)} 건 처리됨")
                            batch_count = 0
        
        db_operation_time = time.time() - db_operation_start
        logger.info(f"DB 저장 소요 시간 ({'벌크' if all_or_nothing else '개별'} 인서트): {db_operation_time:.2f}초")
        
        total_time = time.time() - start_time
        logger.info(f"전체 프로세스 소요 시간: {total_time:.2f}초")
        
        # 결과 반환
        result = {
            "status": "success" if success_count == len(valid_items) else "partial_success" if success_count > 0 else "error",
            "message": "파일 처리가 완료되었습니다.",
            "total_rows": len(df),
            "processed_count": len(valid_items),
            "success_count": success_count,
            "error_count": len(errors) + len(failed_items),
            "validation_errors": errors,
            "failed_items": failed_items,
            "insert_mode": "bulk" if all_or_nothing else "individual",
            "performance_metrics": {
                "file_reading_time": round(file_reading_time, 2),
                "validation_time": round(validation_time, 2),
                "db_operation_time": round(db_operation_time, 2),
                "total_time": round(total_time, 2)
            }
        }
        
        return result
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"치명적 오류: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{item_id}", response_model=ItemResponse)
@log_operation(log_type=LogType.ALL)
async def read_item(
    item_id: int = Path(..., ge=1, description="상품 ID"),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    특정 상품을 조회합니다.
    """
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(SELECT_ITEM_BY_ID, {"item_id": item_id})
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
            
            # 이미지 정보 조회
            cursor.execute(SELECT_ITEM_IMGS, {"item_id": item_id})
            result["images"] = cursor.fetchall()
            
            return result
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"상품 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{item_id}/images", response_model=ItemImage)
@log_operation(log_type=LogType.ALL)
async def add_item_image(
    item_id: int = Path(..., ge=1, description="상품 ID"),
    image: UploadFile = File(...),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    상품에 이미지를 추가합니다.
    """
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            # 상품 존재 여부 확인
            cursor.execute(SELECT_ITEM_BY_ID, {"item_id": item_id})
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
            
            # 이미지 저장 및 상세 정보 추출
            file_info = await save_file(image, FileType.IMAGE)
            original_filename = image.filename
            file_extension = os.path.splitext(image.filename)[1] if image.filename else '.jpg'
            file_size = image.size or 0  # size가 None일 경우 0으로 설정
            
            # 이미지 정보 저장
            cursor.execute(
                ImageQueries.INSERT,
                {
                    "item_id": item_id,
                    "image_path": file_info["path"],
                    "image_filename": file_info["filename"],
                    "original_filename": original_filename,
                    "file_extension": file_extension,
                    "file_size": file_size,
                    "created_at": datetime.now()
                }
            )
            result = cursor.fetchone()
            
            # 이미지 정보 객체 생성
            item_image = ItemImage(
                id=result["id"],
                item_id=item_id,
                image_path=result["image_path"],
                image_filename=result["image_filename"],
                original_filename=original_filename,
                file_extension=file_extension,
                file_size=file_size,
                created_at=result["created_at"]
            )
            
            app_logger.log(
                logging.INFO,
                f"상품 이미지 추가 성공: {result['id']}",
                log_type=LogType.ALL
            )
            return item_image
            
    except Exception as e:
        db.rollback()
        app_logger.log(
            logging.ERROR,
            f"상품 이미지 추가 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{item_id}/images/{img_id}")
@log_operation(log_type=LogType.ALL)
async def delete_item_image(
    item_id: int = Path(..., ge=1, description="상품 ID"),
    img_id: int = Path(..., ge=1, description="이미지 ID"),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    상품의 특정 이미지를 삭제합니다.
    """
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            # 이미지 정보 조회
            cursor.execute(ImageQueries.SELECT_IMAGE_DETAILS, {"img_id": img_id})
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
            
            # 이미지 파일 삭제
            delete_file({
                "path": result["image_path"],
                "filename": result["image_filename"]
            })
            
            # 이미지 정보 삭제
            cursor.execute(ImageQueries.DELETE, {"img_id": img_id})
            
            app_logger.log(
                logging.INFO,
                f"상품 이미지 삭제 성공: {img_id}",
                log_type=LogType.ALL
            )
            return {"message": "이미지가 성공적으로 삭제되었습니다."}
            
    except Exception as e:
        db.rollback()
        app_logger.log(
            logging.ERROR,
            f"상품 이미지 삭제 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{item_id}", response_model=ItemResponse)
@log_operation(log_type=LogType.ALL)
async def update_item(
    item_id: int,
    item: ItemCreate,
    image: Optional[UploadFile] = File(None),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    상품 정보를 업데이트합니다.
    """
    try:
        cursor = db.cursor()
        
        # 기존 상품 정보 조회
        cursor.execute(SELECT_ITEM_BY_ID, {"item_id": item_id})
        existing_item = cursor.fetchone()
        
        if not existing_item:
            raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")
        
        # 상품 정보 업데이트
        update_fields = []
        update_values = []
        
        if item.name is not None:
            update_fields.append("name = %s")
            update_values.append(item.name)
        if item.description is not None:
            update_fields.append("description = %s")
            update_values.append(item.description)
        if item.price is not None:
            update_fields.append("price = %s")
            update_values.append(item.price)
        if item.tax is not None:
            update_fields.append("tax = %s")
            update_values.append(item.tax)
        
        if update_fields:
            update_values.append(item_id)
            cursor.execute(
                UPDATE_ITEM.format(update_fields=", ".join(update_fields)),
                update_values
            )
            result = cursor.fetchone()
        
        # 이미지 업데이트
        if image:
            # 기존 이미지 정보 조회
            cursor.execute(ImageQueries.SELECT_IMAGE_DETAILS, {"item_id": item_id})
            existing_image = cursor.fetchone()
            
            # 새 이미지 저장
            image_info = await save_file(image, FileType.IMAGE)
            original_filename = image.filename
            file_extension = os.path.splitext(image.filename)[1] if image.filename else '.jpg'
            file_size = image.size or 0  # size가 None일 경우 0으로 설정
            
            # 기존 이미지가 있으면 삭제
            if existing_image:
                delete_file({
                    "path": existing_image["image_path"],
                    "filename": existing_image["image_filename"]
                })
                cursor.execute(
                    ImageQueries.UPDATE,
                    {
                        "image_path": image_info["path"],
                        "image_filename": image_info["filename"],
                        "original_filename": original_filename,
                        "file_extension": file_extension,
                        "file_size": file_size,
                        "item_id": item_id
                    }
                )
            else:
                cursor.execute(
                    ImageQueries.INSERT,
                    {
                        "item_id": item_id,
                        "image_path": image_info["path"],
                        "image_filename": image_info["filename"],
                        "original_filename": original_filename,
                        "file_extension": file_extension,
                        "file_size": file_size,
                        "created_at": datetime.now()
                    }
                )
            
            img_result = cursor.fetchone()
            
            # 이미지 정보 객체 생성
            item_image = ItemImage(
                id=img_result["id"],
                item_id=item_id,
                image_path=img_result["image_path"],
                image_filename=img_result["image_filename"],
                original_filename=original_filename,
                file_extension=file_extension,
                file_size=file_size,
                created_at=img_result["created_at"]
            )
        else:
            item_image = None
        
        db.commit()
        
        # 응답 객체 생성
        response = ItemResponse(
            id=item_id,
            name=item.name or existing_item["name"],
            description=item.description or existing_item["description"],
            price=item.price or existing_item["price"],
            tax=item.tax or existing_item["tax"],
            created_at=result["created_at"],
            images=[item_image] if item_image else []
        )
        
        app_logger.log(
            logging.INFO,
            f"상품 업데이트 성공: {item_id}",
            log_type=LogType.ALL
        )
        
        return response
        
    except Exception as e:
        db.rollback()
        app_logger.log(
            logging.ERROR,
            f"상품 업데이트 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{item_id}")
@log_operation(log_type=LogType.ALL)
async def delete_item(
    item_id: int,
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    상품을 삭제합니다.
    """
    try:
        cursor = db.cursor()
        
        # 상품의 모든 이미지 조회
        cursor.execute(ImageQueries.SELECT_IMAGE_DETAILS, {"item_id": item_id})
        images = cursor.fetchall()
        
        # 각 이미지 삭제
        for image in images:
            await delete_item_image(
                item_id=item_id,
                img_id=image["id"],
                db=db
            )
        
        # 상품 삭제
        cursor.execute(DELETE_ITEM, {"item_id": item_id})
        
        db.commit()
        
        app_logger.log(
            logging.INFO,
            f"상품 삭제 성공: {item_id}",
            log_type=LogType.ALL
        )
        
        return {"message": "상품이 성공적으로 삭제되었습니다."}
        
    except Exception as e:
        db.rollback()
        app_logger.log(
            logging.ERROR,
            f"상품 삭제 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))