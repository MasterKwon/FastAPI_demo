"""
사용자 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, status, Path, Query, UploadFile, File
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import EmailStr
from app.database.pool import get_db
from app.utils.logger import log_query, setup_logger, app_logger, LogType
from app.database.exceptions import handle_database_error
from .user_queries import (
    INSERT_USER, SELECT_USER_BY_ID, SELECT_USER_FOR_LOGIN, 
    SELECT_USER_BY_USERNAME, SEARCH_USERS_TEMPLATE,
    UPDATE_USER, DELETE_USER, UPDATE_PASSWORD, SELECT_USER_BY_EMAIL,
    SELECT_USER_COUNT
)
from app.models.users import (
    UserCreate, UserResponse, UserUpdate, UserLogin, UsersResponse,
    UserSortColumn, SortDirection, BulkUploadResponse
)
from enum import Enum
import logging
from datetime import datetime
from app.utils.password import get_password_hash, verify_password
import pandas as pd
import os
import time
import re
    
# 로거 설정
logger = setup_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@log_operation(log_type=LogType.ALL)
async def create_user(
    user: UserCreate,
    db: psycopg2.extensions.connection = Depends(get_db)
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
        with db.cursor() as cursor:
            # 이메일 중복 체크
            cursor.execute(
                SELECT_USER_BY_EMAIL,
                {"email": user.email}
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 이메일입니다."
                )
            
            # 사용자명 중복 체크
            cursor.execute(
                SELECT_USER_BY_USERNAME,
                {"username": user.username}
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 사용자명입니다."
                )
            
            # 비밀번호 해시화
            hashed_password = get_password_hash(user.password)
            
            # 사용자 정보 저장
            cursor.execute(
                INSERT_USER,
                {
                    "username": user.username,
                    "email": user.email,
                    "hashed_password": hashed_password,
                    "is_active": True,
                    "created_at": datetime.now()
                }
            )
            result = cursor.fetchone()
            
            db.commit()
            
            app_logger.log(
                logging.INFO,
                f"사용자 생성 성공: {result['id']}",
                log_type=LogType.ALL
            )
            
            return result
            
    except Exception as e:
        db.rollback()
        app_logger.log(
            logging.ERROR,
            f"사용자 생성 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=UsersResponse)
@log_operation(log_type=LogType.ALL)
async def read_users(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
    db: psycopg2.extensions.connection = Depends(get_db)
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
        with db.cursor() as cursor:
            # 사용자 목록 조회
            query = SEARCH_USERS_TEMPLATE.format(
                where_condition="",
                sort_column=sort_by,
                sort_direction=sort_direction
            )
            cursor.execute(query, {"limit": limit, "offset": skip})
            users = cursor.fetchall()
            
            # 첫 번째 레코드에서 total_count 추출
            total = users[0]["total_count"] if users else 0
            
            # total_count 필드 제거
            for user in users:
                user.pop("total_count", None)
            
            return {
                "users": users,
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
    except Exception as e:
        logger.error(f"사용자 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponse)
@log_operation(log_type=LogType.ALL)
async def read_user(
    user_id: int = Path(..., ge=1, description="사용자 ID"),
    db: psycopg2.extensions.connection = Depends(get_db)
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
        with db.cursor() as cursor:
            cursor.execute(
                SELECT_USER_BY_ID,
                {"user_id": user_id}
            )
            result = cursor.fetchone()
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            return result
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"사용자 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/{email}", response_model=UserResponse)
@log_operation(log_type=LogType.ALL)
async def read_user_by_email(
    email: EmailStr,
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    특정 이메일로 사용자를 조회합니다.
    
    Args:
        email: 조회할 이메일
        
    Returns:
        사용자 정보
        
    Raises:
        HTTPException:
            - 404: 사용자를 찾을 수 없는 경우
            - 500: 데이터베이스 오류 발생 시
    """
    try:
        with db.cursor() as cursor:
            params = {"email": email}
            log_query(cursor, SELECT_USER_BY_EMAIL, params)
            cursor.execute(SELECT_USER_BY_EMAIL, params)
            result = cursor.fetchone()
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return result
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"사용자 조회 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/search/", response_model=List[UserResponse])
@log_operation(log_type=LogType.ALL)
async def search_users(
    username: Optional[str] = None,
    email: Optional[EmailStr] = None,
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    sort_by: str = Query("created_at", description="정렬 기준 컬럼"),
    sort_direction: str = Query("desc", description="정렬 방향 (asc/desc)"),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    사용자를 검색합니다.
    
    Args:
        username: 검색할 사용자명 (부분 일치)
        email: 검색할 이메일 (부분 일치)
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        
    Returns:
        검색된 사용자 목록
    """
    try:
        with db.cursor() as cursor:
            # 동적 쿼리 생성
            where_clauses = []
            params = {"limit": limit, "offset": skip}
            
            if username is not None:
                where_clauses.append("username LIKE %(username)s")
                params["username"] = f"%{username}%"
            
            if email is not None:
                where_clauses.append("email LIKE %(email)s")
                params["email"] = f"%{email}%"
            
            # WHERE 절 구성
            where_condition = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            # 사용자 목록 조회
            query = SEARCH_USERS_TEMPLATE.format(
                where_condition=where_condition,
                sort_column=sort_by,
                sort_direction=sort_direction
            )
            cursor.execute(query, params)
            users = cursor.fetchall()
            
            # 첫 번째 레코드에서 total_count 추출
            total = users[0]["total_count"] if users else 0
            
            # total_count 필드 제거
            for user in users:
                user.pop("total_count", None)
            
            return {
                "users": users,
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
    except Exception as e:
        app_logger.log(
            logging.ERROR,
            f"사용자 검색 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{user_id}", response_model=UserResponse)
@log_operation(log_type=LogType.ALL)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: psycopg2.extensions.connection = Depends(get_db)
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
        with db.cursor() as cursor:
            # 사용자 존재 여부 확인
            cursor.execute(
                SELECT_USER_BY_ID,
                {"user_id": user_id}
            )
            existing_user = cursor.fetchone()
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            # 이메일 변경 시 중복 체크
            if user.email and user.email != existing_user["email"]:
                cursor.execute(
                    SELECT_USER_BY_EMAIL,
                    {"email": user.email}
                )
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="이미 등록된 이메일입니다."
                    )
            
            # 사용자명 변경 시 중복 체크
            if user.username and user.username != existing_user["username"]:
                cursor.execute(
                    SELECT_USER_BY_USERNAME,
                    {"username": user.username}
                )
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="이미 등록된 사용자명입니다."
                    )
            
            # 업데이트할 데이터 준비
            update_data = user.dict(exclude_unset=True)
            if not update_data:
                return existing_user
            
            # 비밀번호가 포함된 경우 해시화
            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
            # 업데이트 쿼리 실행
            cursor.execute(
                UPDATE_USER,
                {
                    "user_id": user_id,
                    **update_data,
                    "updated_at": datetime.now()
                }
            )
            result = cursor.fetchone()
            
            db.commit()
            
            app_logger.log(
                logging.INFO,
                f"사용자 정보 업데이트 성공: {user_id}",
                log_type=LogType.ALL
            )
            
            return result
            
    except Exception as e:
        db.rollback()
        app_logger.log(
            logging.ERROR,
            f"사용자 정보 업데이트 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
@log_operation(log_type=LogType.ALL)
async def delete_user(
    user_id: int,
    db: psycopg2.extensions.connection = Depends(get_db)
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
        with db.cursor() as cursor:
            # 사용자 존재 여부 확인
            cursor.execute(
                SELECT_USER_BY_ID,
                {"user_id": user_id}
            )
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="사용자를 찾을 수 없습니다."
                )
            
            # 사용자 삭제
            cursor.execute(
                DELETE_USER,
                {"user_id": user_id}
            )
            
            db.commit()
            
            app_logger.log(
                logging.INFO,
                f"사용자 삭제 성공: {user_id}",
                log_type=LogType.ALL
            )
            
            return {"message": "사용자가 성공적으로 삭제되었습니다."}
            
    except Exception as e:
        db.rollback()
        app_logger.log(
            logging.ERROR,
            f"사용자 삭제 실패: {str(e)}",
            log_type=LogType.ALL
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
@log_operation(log_type=LogType.ALL)
async def login(
    user: UserLogin,
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    사용자 로그인
    
    Args:
        user: 로그인 정보
        db: 데이터베이스 연결
    
    Returns:
        dict: 사용자 정보
    
    Raises:
        HTTPException: 로그인 실패 시
    """
    try:
        with db.cursor() as cursor:
            # 사용자 조회
            cursor.execute(
                SELECT_USER_FOR_LOGIN,
                {"email": user.email}
            )
            user_data = cursor.fetchone()
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 올바르지 않습니다"
                )
            
            # 계정 비활성화 상태 확인
            if not user_data["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="비활성화된 계정입니다"
                )
            
            # 비밀번호 검증
            if not verify_password(user.password, user_data["hashed_password"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이메일 또는 비밀번호가 올바르지 않습니다"
                )
            
            return user_data
            
    except HTTPException as e:
        logger.error(f"로그인 실패: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"로그인 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/bulk-upload", response_model=BulkUploadResponse)
@log_operation(log_type=LogType.ALL)
async def bulk_upload_users(
    file: UploadFile = File(...),
    db: psycopg2.extensions.connection = Depends(get_db)
):
    """
    엑셀 파일을 이용한 사용자 일괄 등록
    
    Args:
        file: 업로드할 엑셀 파일
        db: 데이터베이스 연결
    
    Returns:
        BulkUploadResponse: 일괄 등록 결과
    """
    try:
        # 엑셀 파일 처리
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), header=0)
        
        # 데이터프레임 기본 정보 로깅
        logger.info(f"[엑셀 파일] 컬럼: {df.columns.tolist()}, 행 수: {len(df)}")
        
        # 필수 컬럼 수 확인
        if len(df.columns) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="필수 컬럼이 부족합니다. 사용자명, 이메일, 비밀번호 순서로 입력해주세요."
            )
        
        # 컬럼 순서로 데이터 추출 및 중복 체크
        try:
            usernames = df.iloc[:, 0].astype(str).str.strip()
            emails = df.iloc[:, 1].astype(str).str.strip()
            
            # 중복 체크
            if emails.duplicated().any():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="중복된 이메일이 있습니다."
                )
            
            if usernames.duplicated().any():
                raise HTTPException(
                    status_code=400,
                    detail="중복된 사용자명이 있습니다."
                )
            
        except Exception as e:
            logger.error(f"[데이터 검증] 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"데이터 검증 중 오류가 발생했습니다: {str(e)}"
            )
        
        # 데이터베이스에 일괄 등록
        cursor = db.cursor()
        created_users = []
        failed_items = []
        
        try:
            for idx, row in df.iterrows():
                try:
                    # 데이터 추출
                    username = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
                    email = str(row.iloc[1]).strip() if not pd.isna(row.iloc[1]) else ""
                    password = str(row.iloc[2]).strip() if not pd.isna(row.iloc[2]) else ""
                    
                    # logger.info(f"[행 {idx + 2}] 처리 시작 - 사용자명: {username}, 이메일: {email}")
                    
                    # 필수 값 검증
                    if not username:
                        raise ValueError("사용자명은 필수입니다")
                    if not email:
                        raise ValueError("이메일은 필수입니다")
                    if not password:
                        raise ValueError("비밀번호는 필수입니다")
                    
                    # 이메일 형식 검증
                    if not "@" in email or not "." in email:
                        raise ValueError(f"유효하지 않은 이메일 형식입니다: {email}")
                    
                    # 한글 이메일 차단
                    if any('\uAC00' <= char <= '\uD7A3' for char in email):
                        raise ValueError(f"한글이 포함된 이메일은 사용할 수 없습니다: {email}")
                    
                    # 이메일 형식 추가 검증
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                        raise ValueError(f"올바른 이메일 형식이 아닙니다: {email}")
                    
                    # 비밀번호 길이 검증
                    if len(password) < 8:
                        raise ValueError("비밀번호는 8자 이상이어야 합니다")
                    
                    # 이메일 중복 확인
                    cursor.execute(
                        SELECT_USER_BY_EMAIL,
                        {"email": email}
                    )
                    if cursor.fetchone():
                        raise ValueError(f"이미 등록된 이메일입니다: {email}")
                    
                    # 사용자명 중복 확인
                    cursor.execute(
                        SELECT_USER_BY_USERNAME,
                        {"username": username}
                    )
                    if cursor.fetchone():
                        raise ValueError(f"이미 등록된 사용자명입니다: {username}")
                    
                    # 비밀번호 해시화
                    hashed_password = get_password_hash(password)
                    
                    # 사용자 생성
                    cursor.execute(
                        INSERT_USER,
                        {
                            "username": username,
                            "email": email,
                            "hashed_password": hashed_password,
                            "is_active": True,
                            "created_at": datetime.now()
                        }
                    )
                    user = cursor.fetchone()
                    created_users.append(user)
                    # logger.info(f"[행 {idx + 2}] 사용자 생성 성공")
                    
                except Exception as e:
                    logger.error(f"[행 {idx + 2}] 처리 실패: {str(e)}")
                    failed_items.append({
                        "row": idx + 2,
                        "username": username if 'username' in locals() else None,
                        "email": email if 'email' in locals() else None,
                        "error": str(e)
                    })
                    continue
            
            if not created_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "유효한 데이터가 없습니다.",
                        "errors": failed_items
                    }
                )
            
            db.commit()
            
            result = {
                "status": "success" if len(failed_items) == 0 else "partial_success",
                "message": "파일 처리가 완료되었습니다.",
                "total_rows": len(df),
                "success_count": len(created_users),
                "error_count": len(failed_items),
                "failed_items": failed_items
            }
            
            logger.info(f"[일괄 등록] 완료 - 성공: {len(created_users)}, 실패: {len(failed_items)}")
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"[일괄 등록] 치명적 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        
    except HTTPException as e:
        logger.error(f"사용자 일괄 등록 실패: {str(e)}")
        raise e
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"사용자 일괄 등록 중 오류 발생:\n"
                    f"오류 유형: {type(e).__name__}\n"
                    f"오류 메시지: {str(e)}\n"
                    f"스택 트레이스:\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 일괄 등록 중 오류가 발생했습니다: {str(e)}"
        ) 