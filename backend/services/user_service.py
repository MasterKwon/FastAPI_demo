"""
사용자 관련 서비스
"""
from datetime import datetime
import logging
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.models.users import UserCreate, UserUpdate, UserResponse
from backend.utils.password import get_password_hash, verify_password
from backend.utils.logger import app_logger, LogType
from backend.database.exceptions import DatabaseError
from backend.queries.user_queries import (
    INSERT_USER, SELECT_USER_BY_ID, SELECT_USER_FOR_LOGIN,
    SELECT_USER_BY_USERNAME, SELECT_USER_BY_EMAIL, SELECT_USERS,
    UPDATE_USER, DELETE_USER, UPDATE_PASSWORD
)

class UserService:
    def __init__(self, db: psycopg2.extensions.connection):
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def create_user(self, user: UserCreate) -> Dict[str, Any]:
        """새로운 사용자를 생성합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # 이메일 중복 체크
                cursor.execute(SELECT_USER_BY_EMAIL, {"email": user.email})
                if cursor.fetchone():
                    raise ValueError("이미 등록된 이메일입니다.")
                
                # 사용자명 중복 체크
                cursor.execute(SELECT_USER_BY_USERNAME, {"username": user.username})
                if cursor.fetchone():
                    raise ValueError("이미 등록된 사용자명입니다.")
                
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
                self.db.commit()
                
                app_logger.log(
                    logging.INFO,
                    f"사용자 생성 성공: {result['id']}",
                    log_type=LogType.ALL
                )
                
                return result
                
        except Exception as e:
            self.db.rollback()
            app_logger.log(
                logging.ERROR,
                f"사용자 생성 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"사용자 생성 실패: {str(e)}")

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_direction: str = "desc"
    ) -> Dict[str, Any]:
        """사용자 목록을 조회합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # 사용자 목록 조회
                query = SELECT_USERS.format(
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
            app_logger.log(
                logging.ERROR,
                f"사용자 목록 조회 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"사용자 목록 조회 실패: {str(e)}")

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """특정 사용자를 조회합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(SELECT_USER_BY_ID, {"user_id": user_id})
                result = cursor.fetchone()
                if not result:
                    raise ValueError("사용자를 찾을 수 없습니다.")
                
                return result
                
        except Exception as e:
            app_logger.log(
                logging.ERROR,
                f"사용자 조회 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"사용자 조회 실패: {str(e)}")

    async def update_user(self, user_id: int, user: UserUpdate) -> Dict[str, Any]:
        """사용자 정보를 업데이트합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # 사용자 존재 여부 확인
                cursor.execute(SELECT_USER_BY_ID, {"user_id": user_id})
                existing_user = cursor.fetchone()
                if not existing_user:
                    raise ValueError("사용자를 찾을 수 없습니다.")
                
                # 이메일 변경 시 중복 체크
                if user.email and user.email != existing_user["email"]:
                    cursor.execute(SELECT_USER_BY_EMAIL, {"email": user.email})
                    if cursor.fetchone():
                        raise ValueError("이미 등록된 이메일입니다.")
                
                # 사용자명 변경 시 중복 체크
                if user.username and user.username != existing_user["username"]:
                    cursor.execute(SELECT_USER_BY_USERNAME, {"username": user.username})
                    if cursor.fetchone():
                        raise ValueError("이미 등록된 사용자명입니다.")
                
                # 업데이트할 데이터 준비
                update_data = user.dict(exclude_unset=True)
                if not update_data:
                    return existing_user
                
                # 비밀번호가 포함된 경우 해시화
                if "password" in update_data:
                    update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
                
                # 업데이트 쿼리 실행
                set_clause = ", ".join([f"{k} = %({k})s" for k in update_data.keys()])
                query = UPDATE_USER.format(set_clause=set_clause)
                
                cursor.execute(
                    query,
                    {
                        "user_id": user_id,
                        **update_data,
                        "updated_at": datetime.now()
                    }
                )
                result = cursor.fetchone()
                
                self.db.commit()
                
                app_logger.log(
                    logging.INFO,
                    f"사용자 정보 업데이트 성공: {user_id}",
                    log_type=LogType.ALL
                )
                
                return result
                
        except Exception as e:
            self.db.rollback()
            app_logger.log(
                logging.ERROR,
                f"사용자 정보 업데이트 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"사용자 정보 업데이트 실패: {str(e)}")

    async def delete_user(self, user_id: int) -> None:
        """사용자를 삭제합니다."""
        try:
            with self.db.cursor() as cursor:
                # 사용자 존재 여부 확인
                cursor.execute(SELECT_USER_BY_ID, {"user_id": user_id})
                if not cursor.fetchone():
                    raise ValueError("사용자를 찾을 수 없습니다.")
                
                # 사용자 삭제
                cursor.execute(DELETE_USER, {"user_id": user_id})
                
                self.db.commit()
                
                app_logger.log(
                    logging.INFO,
                    f"사용자 삭제 성공: {user_id}",
                    log_type=LogType.ALL
                )
                
        except Exception as e:
            self.db.rollback()
            app_logger.log(
                logging.ERROR,
                f"사용자 삭제 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"사용자 삭제 실패: {str(e)}")

    async def verify_user(self, email: str, password: str) -> Dict[str, Any]:
        """사용자 인증을 수행합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(SELECT_USER_FOR_LOGIN, {"email": email})
                user = cursor.fetchone()
                
                if not user:
                    raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다")
                
                if not user["is_active"]:
                    raise ValueError("비활성화된 계정입니다")
                
                if not verify_password(password, user["hashed_password"]):
                    raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다")
                
                return user
                
        except Exception as e:
            app_logger.log(
                logging.ERROR,
                f"사용자 인증 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"사용자 인증 실패: {str(e)}") 