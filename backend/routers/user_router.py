"""
사용자 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, UploadFile, File
from typing import List, Optional
import asyncpg
from pydantic import EmailStr
from backend.database.async_pool import get_async_db
from backend.utils.logger import log_query, setup_logger, app_logger, LogType
from backend.database.exceptions import handle_database_error
from backend.queries.user_queries import (
    INSERT_USER, SELECT_USER_BY_ID, SELECT_USER_FOR_LOGIN, 
    SELECT_USER_BY_USERNAME, SELECT_USERS_TEMPLATE,
    UPDATE_USER, DELETE_USER, UPDATE_PASSWORD, SELECT_USER_BY_EMAIL,
    SELECT_USER_COUNT
)
from backend.models.users import (
    UserCreate, UserResponse, UserUpdate, UserLogin, UsersResponse,
    UserSortColumn, SortDirection, BulkUploadResponse
)
from enum import Enum
import logging
from datetime import datetime
from backend.utils.password import get_password_hash, verify_password
import pandas as pd
import os
import time
import re
from backend.utils.decorators import log_operation
from backend.schemas.common import ResponseModel
from backend.services.user_service import UserService
from io import BytesIO

# 로거 설정
logger = setup_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ResponseModel[UserResponse], status_code=status.HTTP_201_CREATED)
@log_operation(log_type=LogType.ALL)
async def create_user(
    user: UserCreate,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    새로운 사용자를 생성합니다.
    
    Args:
        user: 생성할 사용자 정보
        
    Returns:
        생성된 사용자 정보
        
    Raises:
        HTTPException: 
            - 400: 이메일이 이미 등록된 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 이메일 중복 체크
        email_exists = await db.fetchrow(
            SELECT_USER_BY_EMAIL,
            user.email
        )
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다."
            )
        
        # 사용자명 중복 체크
        username_exists = await db.fetchrow(
            SELECT_USER_BY_USERNAME,
            user.username
        )
        if username_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 사용자명입니다."
            )
        
        # 비밀번호 해시화
        hashed_password = get_password_hash(user.password)
        
        # 사용자 정보 저장
        result = await db.fetchrow(
            INSERT_USER,
            user.username,
            user.email,
            hashed_password,
            True,
            datetime.now()
        )
        
        app_logger.log(
            logging.INFO,
            f"사용자 생성 성공: {result['id']}",
            log_type=LogType.ALL
        )
        
        return ResponseModel(data=result, message="User created successfully", status_code=201)
        
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"사용자 생성 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=ResponseModel[UsersResponse])
@log_operation(log_type=LogType.ALL)
async def read_users(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    모든 사용자 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        sort_by: 정렬 기준 컬럼 (기본값: created_at)
        sort_direction: 정렬 방향 (기본값: desc)
        
    Returns:
        사용자 목록과 페이지네이션 정보
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        # 사용자 목록 조회
        query = SELECT_USERS_TEMPLATE.format(
            where_condition="",
            sort_column=sort_by,
            sort_direction=sort_direction
        )
        users = await db.fetch(query, limit, skip)
        
        # 첫 번째 레코드에서 total_count 추출
        total = users[0]["total_count"] if users else 0
        
        # total_count 필드 제거
        for user in users:
            user.pop("total_count", None)
        
        return ResponseModel(data={
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit
        }, message="Users retrieved successfully")
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )

@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
@log_operation(log_type=LogType.ALL)
async def read_user(
    user_id: int = Path(..., ge=1, description="사용자 ID"),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    특정 사용자를 조회합니다.
    
    Args:
        user_id: 조회할 사용자 ID
        
    Returns:
        사용자 정보
        
    Raises:
        HTTPException:
            - 404: 사용자를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        user = await db.fetchrow(
            SELECT_USER_BY_ID,
            user_id
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return ResponseModel(data=user, message="User retrieved successfully")
        
    except Exception as e:
        logger.error(f"사용자 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/email/{email}", response_model=ResponseModel[UserResponse])
@log_operation(log_type=LogType.ALL)
async def read_user_by_email(
    email: EmailStr,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    이메일로 사용자를 조회합니다.
    
    Args:
        email: 조회할 사용자의 이메일
        
    Returns:
        사용자 정보
        
    Raises:
        HTTPException:
            - 404: 사용자를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        user = await db.fetchrow(
            SELECT_USER_BY_EMAIL,
            email
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return ResponseModel(data=user, message="User retrieved successfully")
        
    except Exception as e:
        logger.error(f"이메일로 사용자 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/search/", response_model=ResponseModel[List[UserResponse]])
@log_operation(log_type=LogType.ALL)
async def search_users(
    username: Optional[str] = None,
    email: Optional[EmailStr] = None,
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    사용자를 검색합니다.
    
    Args:
        username: 검색할 사용자명 (선택)
        email: 검색할 이메일 (선택)
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        sort_by: 정렬 기준 컬럼 (기본값: created_at)
        sort_direction: 정렬 방향 (기본값: desc)
        
    Returns:
        검색된 사용자 목록
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        # 검색 조건 구성
        conditions = []
        if username:
            conditions.append(f"username ILIKE '%{username}%'")
        if email:
            conditions.append(f"email ILIKE '%{email}%'")
        
        where_condition = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # 사용자 검색
        query = SELECT_USERS_TEMPLATE.format(
            where_condition=where_condition,
            sort_column=sort_by,
            sort_direction=sort_direction
        )
        users = await db.fetch(query, limit, skip)
        
        # total_count 필드 제거
        for user in users:
            user.pop("total_count", None)
        
        return ResponseModel(data=users, message="Users retrieved successfully")
        
    except Exception as e:
        logger.error(f"사용자 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )

@router.put("/{user_id}", response_model=ResponseModel[UserResponse])
@log_operation(log_type=LogType.ALL)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    사용자 정보를 업데이트합니다.
    
    Args:
        user_id: 업데이트할 사용자 ID
        user: 업데이트할 사용자 정보
        
    Returns:
        업데이트된 사용자 정보
        
    Raises:
        HTTPException:
            - 404: 사용자를 찾을 수 없는 경우
            - 400: 이메일이 이미 등록된 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 사용자 존재 여부 확인
        existing_user = await db.fetchrow(
            SELECT_USER_BY_ID,
            user_id
        )
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # 이메일 중복 체크
        if user.email and user.email != existing_user["email"]:
            email_exists = await db.fetchrow(
                SELECT_USER_BY_EMAIL,
                user.email
            )
            if email_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 이메일입니다."
                )
        
        # 사용자 정보 업데이트
        result = await db.fetchrow(
            UPDATE_USER,
            user_id,
            user.username,
            user.email,
            user.is_active
        )
        
        return ResponseModel(data=result, message="User updated successfully")
        
    except Exception as e:
        logger.error(f"사용자 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
    )

@router.delete("/{user_id}", response_model=ResponseModel)
@log_operation(log_type=LogType.ALL)
async def delete_user(
    user_id: int,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    사용자를 삭제합니다.
    
    Args:
        user_id: 삭제할 사용자 ID
        
    Returns:
        삭제 결과
        
    Raises:
        HTTPException:
            - 404: 사용자를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 사용자 존재 여부 확인
        existing_user = await db.fetchrow(
            SELECT_USER_BY_ID,
            user_id
        )
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # 사용자 삭제
        await db.execute(
            DELETE_USER,
            user_id
        )
        
        return ResponseModel(message="User deleted successfully")
        
    except Exception as e:
        logger.error(f"사용자 삭제 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/login")
@log_operation(log_type=LogType.ALL)
async def login(
    user: UserLogin,
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    사용자 로그인을 처리합니다.
    
    Args:
        user: 로그인 정보 (이메일, 비밀번호)
        
    Returns:
        로그인 결과
        
    Raises:
        HTTPException:
            - 401: 이메일 또는 비밀번호가 잘못된 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        # 사용자 조회
        db_user = await db.fetchrow(
            SELECT_USER_FOR_LOGIN,
            user.email
        )
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # 비밀번호 검증
        if not verify_password(user.password, db_user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # 비밀번호 필드 제거
        db_user.pop("hashed_password", None)
        
        return ResponseModel(data=db_user, message="Login successful")
        
    except Exception as e:
        logger.error(f"로그인 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/bulk-upload", response_model=ResponseModel[BulkUploadResponse])
@log_operation(log_type=LogType.ALL)
async def bulk_upload_users(
    file: UploadFile = File(...),
    db: asyncpg.Connection = Depends(get_async_db)
):
    """
    엑셀 파일을 통해 사용자를 대량 등록합니다.
    
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
        required_columns = ['username', 'email', 'password']
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
                    # 이메일 중복 체크
                    email_exists = await db.fetchrow(
                        SELECT_USER_BY_EMAIL,
                        row['email']
                    )
                    if email_exists:
                        errors.append(f"Row {index + 2}: Email already exists")
                        error_count += 1
                        continue
                    
                    # 사용자명 중복 체크
                    username_exists = await db.fetchrow(
                        SELECT_USER_BY_USERNAME,
                        row['username']
                    )
                    if username_exists:
                        errors.append(f"Row {index + 2}: Username already exists")
                        error_count += 1
                        continue
                    
                    # 비밀번호 해시화
                    hashed_password = get_password_hash(row['password'])
                    
                    # 사용자 생성
                    await db.execute(
                        INSERT_USER,
                        row['username'],
                        row['email'],
                        hashed_password,
                        True,
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