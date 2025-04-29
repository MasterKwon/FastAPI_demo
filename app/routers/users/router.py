from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, EmailStr, Field
from app.database.connection import get_db_connection
from app.utils.logger import log_query, setup_logger
from app.database.exceptions import handle_database_error
from passlib.context import CryptContext
from .queries import INSERT_USER, SELECT_USER_BY_ID, SELECT_USER_BY_EMAIL, SELECT_ALL_USERS, SELECT_USER_BY_USERNAME, SEARCH_USERS_TEMPLATE

# 로거 설정
logger = setup_logger("users")

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    """사용자 생성 요청 모델"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, description="비밀번호")
    full_name: Optional[str] = Field(None, max_length=100, description="사용자 전체 이름")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User"
            }
        }

class UserResponse(BaseModel):
    """사용자 응답 모델"""
    id: int = Field(..., description="사용자 ID")
    email: EmailStr = Field(..., description="이메일 주소")
    full_name: Optional[str] = Field(None, description="사용자 전체 이름")
    is_active: bool = Field(..., description="활성화 여부")

    class Config:
        from_attributes = True

def get_password_hash(password: str) -> str:
    """비밀번호를 해시화하는 함수"""
    return pwd_context.hash(password)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: psycopg2.extensions.connection = Depends(get_db_connection)):
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
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(SELECT_USER_BY_EMAIL, {"email": user.email})
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # 비밀번호 해싱
        hashed_password = get_password_hash(user.password)
        
        # 사용자 생성
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            user_data = {
                "email": user.email,
                "hashed_password": hashed_password,
                "full_name": user.full_name
            }
            log_query(cursor, INSERT_USER, user_data)
            cursor.execute(INSERT_USER, user_data)
            result = cursor.fetchone()
            db.commit()
            return result
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(10, ge=1, le=100, description="반환할 최대 레코드 수"),
    db: psycopg2.extensions.connection = Depends(get_db_connection)
):
    """
    모든 사용자 목록을 조회합니다.
    
    Args:
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 10)
        
    Returns:
        사용자 목록
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            params = {"skip": skip, "limit": limit}
            log_query(cursor, SELECT_ALL_USERS, params)
            cursor.execute(SELECT_ALL_USERS, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"사용자 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/search/", response_model=List[UserResponse])
async def search_users(
    username: Optional[str] = None,
    email: Optional[EmailStr] = None,
    skip: int = 0,
    limit: int = 100,
    db: psycopg2.extensions.connection = Depends(get_db_connection)
):
    """
    사용자를 검색합니다.
    
    Args:
        username: 검색할 사용자명 (부분 일치)
        email: 검색할 이메일 (부분 일치)
        skip: 건너뛸 레코드 수 (기본값: 0)
        limit: 반환할 최대 레코드 수 (기본값: 100)
        
    Returns:
        검색된 사용자 목록
        
    Raises:
        HTTPException: 500 - 데이터베이스 오류 발생 시
    """
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            # 동적 쿼리 생성
            where_clauses = []
            params = {"limit": limit, "offset": skip}
            
            if username is not None:
                where_clauses.append("username LIKE %(username)s")
                params["username"] = f"%{username}%"
            
            if email is not None:
                where_clauses.append("email LIKE %(email)s")
                params["email"] = f"%{email}%"
            
            # WHERE 절이 있는 경우에만 추가
            where_clause = " AND ".join(where_clauses)
            query = SEARCH_USERS_TEMPLATE.format(where_clause=where_clause) if where_clause else SELECT_ALL_USERS
            
            log_query(cursor, query, params)
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"사용자 검색 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int = Path(..., ge=1, description="사용자 ID"),
    db: psycopg2.extensions.connection = Depends(get_db_connection)
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
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
            params = {"user_id": user_id}
            log_query(cursor, SELECT_USER_BY_ID, params)
            cursor.execute(SELECT_USER_BY_ID, params)
            result = cursor.fetchone()
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return result
    except Exception as e:
        logger.error(f"사용자 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/email/{email}", response_model=UserResponse)
async def read_user_by_email(
    email: EmailStr,
    db: psycopg2.extensions.connection = Depends(get_db_connection)
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
        with db.cursor(cursor_factory=RealDictCursor) as cursor:
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
        logger.error(f"사용자 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 