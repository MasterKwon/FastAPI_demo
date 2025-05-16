"""
리뷰 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from typing import List, Optional
import asyncpg
from backend.database.async_pool import get_async_db
from backend.utils.logger import setup_logger, app_logger, LogType
from backend.database.exceptions import handle_database_error
from backend.queries.review_queries import (
    INSERT_REVIEW, SELECT_REVIEW_BY_ID, SELECT_REVIEWS_TEMPLATE,
    UPDATE_REVIEW, DELETE_REVIEW, SELECT_REVIEW_COUNT
)
from backend.models.reviews import (
    ReviewCreate, ReviewResponse, ReviewUpdate, ReviewsResponse,
    ReviewSortColumn, SortDirection
)
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
async def create_review(
    review: ReviewCreate,
    db: asyncpg.Connection = Depends(get_async_db)
):
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
        # 리뷰 정보 저장
        result = await db.fetchrow(
            INSERT_REVIEW,
            review.user_id,
            review.item_id,
            review.rating,
            review.comment,
            datetime.now()
        )
        
        app_logger.log(
            logging.INFO,
            f"리뷰 생성 성공: {result['id']}",
            log_type=LogType.ALL
        )
        
        return ResponseModel(data=result, message="Review created successfully", status_code=201)
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"리뷰 생성 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=ResponseModel[ReviewsResponse])
@log_operation(log_type=LogType.ALL)
async def read_reviews(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
    db: asyncpg.Connection = Depends(get_async_db)
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
        # 리뷰 목록 조회
        query = SELECT_REVIEWS_TEMPLATE.format(
            where_condition="",
            sort_column=sort_by,
            sort_direction=sort_direction
        )
        reviews = await db.fetch(query, limit, skip)
        
        # 첫 번째 레코드에서 total_count 추출
        total = reviews[0]["total_count"] if reviews else 0
        
        # total_count 필드 제거
        for review in reviews:
            review.pop("total_count", None)
        
        return ResponseModel(data={
            "reviews": reviews,
            "total": total,
            "skip": skip,
            "limit": limit
        }, message="Reviews retrieved successfully")
        
    except Exception as e:
        logger.error(f"리뷰 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{review_id}", response_model=ResponseModel[ReviewResponse])
@log_operation(log_type=LogType.ALL)
async def read_review(
    review_id: int = Path(..., ge=1, description="리뷰 ID"),
    db: asyncpg.Connection = Depends(get_async_db)
):
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
        review = await db.fetchrow(
            SELECT_REVIEW_BY_ID,
            review_id
        )
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        return ResponseModel(data=review, message="Review retrieved successfully")
        
    except Exception as e:
        logger.error(f"리뷰 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/search/", response_model=ResponseModel[List[ReviewResponse]])
@log_operation(log_type=LogType.ALL)
async def search_reviews(
    user_id: Optional[int] = None,
    item_id: Optional[int] = None,
    rating: Optional[int] = None,
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    리뷰를 검색합니다.
    
    Args:
        user_id: 검색할 사용자 ID (선택)
        item_id: 검색할 아이템 ID (선택)
        rating: 검색할 평점 (선택)
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        sort_by: 정렬 기준 컬럼 (기본값: created_at)
        sort_direction: 정렬 방향 (기본값: desc)
        
    Returns:
        검색된 리뷰 목록
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        # 검색 조건 구성
        conditions = []
        if user_id is not None:
            conditions.append(f"user_id = {user_id}")
        if item_id is not None:
            conditions.append(f"item_id = {item_id}")
        if rating is not None:
            conditions.append(f"rating = {rating}")
        
        where_condition = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # 리뷰 검색
        query = SELECT_REVIEWS_TEMPLATE.format(
            where_condition=where_condition,
            sort_column=sort_by,
            sort_direction=sort_direction
        )
        reviews = await db.fetch(query, limit, skip)
        
        # total_count 필드 제거
        for review in reviews:
            review.pop("total_count", None)
        
        return ResponseModel(data=reviews, message="Reviews retrieved successfully")
        
    except Exception as e:
        logger.error(f"리뷰 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{review_id}", response_model=ResponseModel[ReviewResponse])
@log_operation(log_type=LogType.ALL)
async def update_review(
    review_id: int,
    review: ReviewUpdate,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    리뷰 정보를 업데이트합니다.
    
    Args:
        review_id: 업데이트할 리뷰 ID
        review: 업데이트할 리뷰 정보
        
    Returns:
        업데이트된 리뷰 정보
        
    Raises:
        HTTPException:
            - 404: 리뷰를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 리뷰 존재 여부 확인
        existing_review = await db.fetchrow(
            SELECT_REVIEW_BY_ID,
            review_id
        )
        if not existing_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # 리뷰 정보 업데이트
        result = await db.fetchrow(
            UPDATE_REVIEW,
            review_id,
            review.rating,
            review.comment
        )
        
        return ResponseModel(data=result, message="Review updated successfully")
        
    except Exception as e:
        logger.error(f"리뷰 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{review_id}", response_model=ResponseModel)
@log_operation(log_type=LogType.ALL)
async def delete_review(
    review_id: int,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    리뷰를 삭제합니다.
    
    Args:
        review_id: 삭제할 리뷰 ID
        
    Returns:
        삭제 결과
        
    Raises:
        HTTPException:
            - 404: 리뷰를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 리뷰 존재 여부 확인
        existing_review = await db.fetchrow(
            SELECT_REVIEW_BY_ID,
            review_id
        )
        if not existing_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # 리뷰 삭제
        await db.execute(
            DELETE_REVIEW,
            review_id
        )
        
        return ResponseModel(message="Review deleted successfully")
        
    except Exception as e:
        logger.error(f"리뷰 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 