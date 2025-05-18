"""
상품 리뷰 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from typing import List, Optional
import asyncpg
from backend.database.async_pool import get_async_db, async_db_pool
from backend.utils.logger import setup_logger, app_logger, LogType
from backend.database.exceptions import handle_database_error
from backend.queries.item_review_queries import (
    INSERT_ITEM_REVIEW, SELECT_ITEM_REVIEW_BY_ID, SELECT_ITEM_REVIEWS_TEMPLATE,
    UPDATE_ITEM_REVIEW, DELETE_ITEM_REVIEW, SELECT_ITEM_REVIEW_COUNT
)
from backend.schemas.item_review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ItemReviewSortColumn
)
from backend.schemas.item_review_list import ReviewListResponse
from enum import Enum
import logging
from datetime import datetime
from backend.utils.decorators import log_operation
from backend.schemas.common import ResponseModel

# 로거 설정
logger = setup_logger(__name__)

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ResponseModel[ReviewResponse], status_code=status.HTTP_201_CREATED)
@log_operation(log_type=LogType.ALL)
async def create_review(review: ReviewCreate):
    """
    새로운 리뷰를 생성합니다.
    
    Args:
        review: 생성할 리뷰 정보
        
    Returns:
        생성된 리뷰 정보
        
    Raises:
        HTTPException: 
            - 400: 유효하지 않은 데이터인 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 리뷰 정보 저장
            result = await async_db_pool.fetchrow(
                conn,
                INSERT_ITEM_REVIEW,
                review.item_id,
                review.usr_id,
                review.review_content,
                review.score
            )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_REVIEW_ROUTER] 리뷰 생성 완료: {result['id']}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=result, message="Review created successfully", status_code=201)
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_REVIEW_ROUTER] 리뷰 생성 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=ResponseModel[ReviewListResponse])
@log_operation(log_type=LogType.ALL)
async def read_reviews(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: ItemReviewSortColumn = Query(ItemReviewSortColumn.created_at, description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)")
):
    """
    모든 리뷰 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        sort_by: 정렬 기준 컬럼 (기본값: created_at)
        sort_direction: 정렬 방향 (기본값: desc)
        
    Returns:
        리뷰 목록과 페이지네이션 정보
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 리뷰 목록 조회
            query = SELECT_ITEM_REVIEWS_TEMPLATE.format(
                where_condition="",
                sort_column=sort_by,
                sort_direction=sort_direction
            )
            reviews = await async_db_pool.fetch(
                conn,
                query,
                limit,
                skip
            )
            
            # 첫 번째 레코드에서 total_count 추출
            total = reviews[0]["total_count"] if reviews else 0
            
            # total_count 필드 제거
            for review in reviews:
                review.pop("total_count", None)
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_REVIEW_ROUTER] 리뷰 목록 조회 완료: {len(reviews)}개",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data={
                "reviews": reviews,
                "total": total,
                "skip": skip,
                "limit": limit
            }, message="Reviews retrieved successfully")
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_REVIEW_ROUTER] 리뷰 목록 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{review_id}", response_model=ResponseModel[ReviewResponse])
@log_operation(log_type=LogType.ALL)
async def read_review(review_id: int = Path(..., ge=1, description="리뷰 ID")):
    """
    특정 리뷰를 조회합니다.
    
    Args:
        review_id: 조회할 리뷰 ID
        
    Returns:
        리뷰 정보
        
    Raises:
        HTTPException:
            - 404: 리뷰를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            review = await async_db_pool.fetchrow(
                conn,
                SELECT_ITEM_REVIEW_BY_ID,
                review_id
            )
            
            if not review:
                app_logger.log(
                    logging.WARNING,
                    f"[ITEM_REVIEW_ROUTER] 리뷰를 찾을 수 없음: {review_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found"
                )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_REVIEW_ROUTER] 리뷰 상세 조회 완료: {review_id}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=review, message="Review retrieved successfully")
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_REVIEW_ROUTER] 리뷰 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{review_id}", response_model=ResponseModel[ReviewResponse])
@log_operation(log_type=LogType.ALL)
async def update_review(
    review_id: int = Path(..., ge=1, description="리뷰 ID"),
    review: ReviewUpdate = None
):
    """
    리뷰를 수정합니다.
    
    Args:
        review_id: 수정할 리뷰 ID
        review: 수정할 리뷰 정보
        
    Returns:
        수정된 리뷰 정보
        
    Raises:
        HTTPException:
            - 404: 리뷰를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 리뷰 존재 확인
            exists = await async_db_pool.fetchrow(
                conn,
                "SELECT EXISTS(SELECT 1 FROM item_reviews WHERE id = $1)",
                review_id
            )
            
            if not exists:
                app_logger.log(
                    logging.WARNING,
                    f"[ITEM_REVIEW_ROUTER] 리뷰를 찾을 수 없음: {review_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found"
                )
            
            # 리뷰 수정
            result = await async_db_pool.fetchrow(
                conn,
                UPDATE_ITEM_REVIEW,
                review_id,
                review.review_content,
                review.score
            )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_REVIEW_ROUTER] 리뷰 수정 완료: {review_id}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=result, message="Review updated successfully")
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_REVIEW_ROUTER] 리뷰 수정 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{review_id}", response_model=ResponseModel)
@log_operation(log_type=LogType.ALL)
async def delete_review(review_id: int = Path(..., ge=1, description="리뷰 ID")):
    """
    리뷰를 삭제합니다.
    
    Args:
        review_id: 삭제할 리뷰 ID
        
    Returns:
        삭제 성공 메시지
        
    Raises:
        HTTPException:
            - 404: 리뷰를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 리뷰 존재 확인
            exists = await async_db_pool.fetchrow(
                conn,
                "SELECT EXISTS(SELECT 1 FROM item_reviews WHERE id = $1)",
                review_id
            )
            
            if not exists:
                app_logger.log(
                    logging.WARNING,
                    f"[ITEM_REVIEW_ROUTER] 리뷰를 찾을 수 없음: {review_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found"
                )
            
            # 리뷰 삭제
            await async_db_pool.execute_query(
                conn,
                DELETE_ITEM_REVIEW,
                review_id
            )
            
            app_logger.log(
                logging.INFO,
                f"[ITEM_REVIEW_ROUTER] 리뷰 삭제 완료: {review_id}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(message="Review deleted successfully")
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"[ITEM_REVIEW_ROUTER] 리뷰 삭제 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 