"""
사용자 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, UploadFile, File
from typing import List, Optional, Dict, Any
import asyncpg
from pydantic import EmailStr
from backend.database.async_pool import get_async_db, async_db_pool
from backend.utils.logger import log_query, setup_logger, app_logger, LogType
from backend.database.exceptions import handle_database_error
from backend.queries.user_queries import (
    INSERT_USER, SELECT_USER_BY_ID, SELECT_USER_FOR_LOGIN, 
    SELECT_USER_BY_USERNAME, SELECT_USERS_TEMPLATE,
    UPDATE_USER, DELETE_USER, UPDATE_PASSWORD, SELECT_USER_BY_EMAIL,
    SELECT_USER_COUNT
)
from backend.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserLogin
)
from backend.schemas.user_list import UserListResponse
from enum import Enum
import logging
from datetime import datetime
from backend.utils.password import get_password_hash, verify_password
from backend.utils.decorators import log_operation
from backend.schemas.common import ResponseModel
import pandas as pd
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
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 이메일 중복 체크
            existing_user = await async_db_pool.fetchrow(
                conn,
                SELECT_USER_BY_EMAIL,
                user.email
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 이메일입니다."
                )
            
            # 사용자명 중복 체크
            username_exists = await async_db_pool.fetchrow(
                conn,
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
            result = await async_db_pool.fetchrow(
                conn,
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

@router.get("/", response_model=ResponseModel[UserListResponse])
@log_operation(log_type=LogType.ALL)
async def read_users(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: UserListResponse.SortColumn = Query(UserListResponse.SortColumn.created_at, description="정렬 기준 컬럼"),
    sort_direction: UserListResponse.SortDirection = Query(UserListResponse.SortDirection.desc, description="정렬 방향 (asc/desc)"),
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
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 사용자 목록 조회
            query = SELECT_USERS_TEMPLATE.format(
                where_condition="",
                sort_column=sort_by,
                sort_direction=sort_direction
            )
            users = await async_db_pool.fetch(
                conn,
                query,
                limit,
                skip
            )
            
            # 첫 번째 레코드에서 total_count 추출
            total = users[0]["total_count"] if users else 0
            
            # total_count 필드 제거
            for user in users:
                user.pop("total_count", None)
            
            app_logger.log(
                logging.INFO,
                f"사용자 목록 조회 완료: {len(users)}개",
                log_type=LogType.ALL
            )
            
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
        pool = get_async_db()
        async with pool.acquire() as conn:
            row = await async_db_pool.fetchrow(
                conn,
                SELECT_USER_BY_ID,
                user_id
            )
            
            if not row:
                app_logger.log(
                    logging.WARNING,
                    f"[USER_ROUTER] 사용자를 찾을 수 없음: {user_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            app_logger.log(
                logging.INFO,
                f"[USER_ROUTER] 사용자 상세 조회 완료: {user_id}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=UserResponse(**dict(row)), message="User retrieved successfully")
            
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
        pool = get_async_db()
        async with pool.acquire() as conn:
            row = await async_db_pool.fetchrow(
                conn,
                SELECT_USER_BY_EMAIL,
                email
            )
            
            if not row:
                app_logger.log(
                    logging.WARNING,
                    f"[USER_ROUTER] 사용자를 찾을 수 없음: {email}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            app_logger.log(
                logging.INFO,
                f"[USER_ROUTER] 이메일로 사용자 조회 완료: {email}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=UserResponse(**dict(row)), message="User retrieved successfully")
            
    except Exception as e:
        logger.error(f"이메일로 사용자 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{user_id}", response_model=ResponseModel[UserResponse])
@log_operation(log_type=LogType.ALL)
async def update_user(
    user_id: int = Path(..., ge=1, description="사용자 ID"),
    user: UserUpdate = None,
):
    """
    사용자 정보를 수정합니다.
    
    Args:
        user_id: 수정할 사용자 ID
        user: 수정할 사용자 정보
        
    Returns:
        수정된 사용자 정보
        
    Raises:
        HTTPException:
            - 404: 사용자를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 사용자 존재 확인
            exists = await async_db_pool.fetchrow(
                conn,
                "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
                user_id
            )
            
            if not exists:
                app_logger.log(
                    logging.WARNING,
                    f"[USER_ROUTER] 사용자를 찾을 수 없음: {user_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 사용자 수정
            row = await async_db_pool.fetchrow(
                conn,
                UPDATE_USER,
                user_id,
                user.username,
                user.email,
                user.is_active
            )
            
            app_logger.log(
                logging.INFO,
                f"[USER_ROUTER] 사용자 수정 완료: {user_id}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(data=UserResponse(**dict(row)), message="User updated successfully")
            
    except Exception as e:
        logger.error(f"사용자 수정 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{user_id}", response_model=ResponseModel)
@log_operation(log_type=LogType.ALL)
async def delete_user(
    user_id: int = Path(..., ge=1, description="사용자 ID"),
):
    """
    사용자를 삭제합니다.
    
    Args:
        user_id: 삭제할 사용자 ID
        
    Returns:
        삭제 성공 메시지
        
    Raises:
        HTTPException:
            - 404: 사용자를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 사용자 존재 확인
            exists = await async_db_pool.fetchrow(
                conn,
                "SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)",
                user_id
            )
            
            if not exists:
                app_logger.log(
                    logging.WARNING,
                    f"[USER_ROUTER] 사용자를 찾을 수 없음: {user_id}",
                    log_type=LogType.ALL
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 사용자 삭제
            await async_db_pool.execute_query(
                conn,
                DELETE_USER,
                user_id
            )
            
            app_logger.log(
                logging.INFO,
                f"[USER_ROUTER] 사용자 삭제 완료: {user_id}",
                log_type=LogType.ALL
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
):
    """
    사용자 로그인
    
    Args:
        user: 로그인 정보 (이메일, 비밀번호)
        
    Returns:
        로그인 성공 메시지와 사용자 정보
        
    Raises:
        HTTPException:
            - 401: 이메일 또는 비밀번호가 일치하지 않는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 사용자 조회
            db_user = await async_db_pool.fetchrow(
                conn,
                SELECT_USER_FOR_LOGIN,
                user.email
            )
            
            if not db_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 일치하지 않습니다."
                )
            
            # 비밀번호 검증
            if not verify_password(user.password, db_user["hashed_password"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 일치하지 않습니다."
                )
            
            app_logger.log(
                logging.INFO,
                f"[USER_ROUTER] 로그인 성공: {user.email}",
                log_type=LogType.ALL
            )
            
            return ResponseModel(
                data={
                    "id": db_user["id"],
                    "username": db_user["username"],
                    "email": db_user["email"]
                },
                message="Login successful"
            )
            
    except Exception as e:
        logger.error(f"로그인 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/search", response_model=ResponseModel[List[UserResponse]])
@log_operation(log_type=LogType.ALL)
async def search_users(
    query: str = Query(..., min_length=2, description="검색어"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
):
    """
    사용자 검색
    
    Args:
        query: 검색어 (최소 2자 이상)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        skip: 건너뛸 레코드 수 (기본값: 0)
        sort_by: 정렬 기준 컬럼 (기본값: created_at)
        sort_direction: 정렬 방향 (기본값: desc)
        
    Returns:
        검색된 사용자 목록
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        pool = get_async_db()
        async with pool.acquire() as conn:
            # 검색 쿼리 생성
            search_condition = f"""
                WHERE username ILIKE $1 
                OR email ILIKE $1 
                OR full_name ILIKE $1
            """
            
            # 정렬 조건 추가
            order_by = f"ORDER BY {sort_by} {sort_direction}"
            
            # 전체 쿼리 생성
            query = f"""
                {SELECT_USERS_TEMPLATE.format(
                    where_condition=search_condition,
                    sort_column=sort_by,
                    sort_direction=sort_direction
                )}
                {order_by}
                LIMIT $2 OFFSET $3
            """
            
            # 검색어에 와일드카드 추가
            search_term = f"%{query}%"
            
            # 검색 실행
            users = await async_db_pool.fetch(
                conn,
                query,
                search_term,
                limit,
                skip
            )
            
            app_logger.log(
                logging.INFO,
                f"[USER_ROUTER] 사용자 검색 완료: {len(users)}개",
                log_type=LogType.ALL
            )
            
            return ResponseModel(
                data=users,
                message="Users retrieved successfully"
            )
            
    except Exception as e:
        logger.error(f"사용자 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/bulk-upload", response_model=ResponseModel[Dict[str, Any]])
@log_operation(log_type=LogType.ALL)
async def bulk_upload_users(
    file: UploadFile = File(...),
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
        
        pool = get_async_db()
        async with pool.acquire() as conn:
            async with conn.transaction():
                for index, row in df.iterrows():
                    try:
                        # 이메일 중복 체크
                        email_exists = await async_db_pool.fetchrow(
                            conn,
                            SELECT_USER_BY_EMAIL,
                            row['email']
                        )
                        if email_exists:
                            errors.append(f"Row {index + 2}: Email already exists")
                            error_count += 1
                            continue
                        
                        # 사용자명 중복 체크
                        username_exists = await async_db_pool.fetchrow(
                            conn,
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
                        await async_db_pool.execute(
                            conn,
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
        
        app_logger.log(
            logging.INFO,
            f"[USER_ROUTER] 대량 업로드 완료: {success_count}개 성공, {error_count}개 실패",
            log_type=LogType.ALL
        )
        
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