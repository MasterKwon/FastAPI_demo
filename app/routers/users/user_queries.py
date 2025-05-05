"""
사용자 관련 SQL 쿼리
"""
from typing import Dict, Any

# 사용자 생성
INSERT_USER = """
INSERT INTO users (username, email, hashed_password, is_active, created_at)
VALUES (%(username)s, %(email)s, %(hashed_password)s, %(is_active)s, %(created_at)s)
RETURNING id, username, email, is_active, created_at;
"""

# 모든 사용자 조회
SELECT_ALL_USERS = """
SELECT id, username, email, is_active, created_at
FROM users
ORDER BY {sort_column} {sort_direction}
LIMIT %(limit)s OFFSET %(skip)s;
"""

# 특정 사용자 조회
SELECT_USER_BY_ID = """
SELECT id, username, email, is_active, created_at
FROM users
WHERE id = %(user_id)s;
"""

# 이메일로 사용자 조회
SELECT_USER_BY_EMAIL = """
SELECT id, username, email, is_active, created_at
FROM users
WHERE email = %(email)s;
"""

# 사용자명으로 사용자 조회
SELECT_USER_BY_USERNAME = """
SELECT id, username, email, is_active, created_at
FROM users
WHERE username = %(username)s;
"""

# 로그인을 위한 사용자 조회
SELECT_USER_FOR_LOGIN = """
SELECT id, username, email, hashed_password, is_active, created_at
FROM users
WHERE email = %(email)s;
"""

# 사용자 검색 쿼리 템플릿
SEARCH_USERS_TEMPLATE = """
SELECT id, username, email, is_active, created_at
FROM users
{where_condition}
ORDER BY {sort_column} {sort_direction}
LIMIT %(limit)s OFFSET %(offset)s;
"""

# 사용자 업데이트
UPDATE_USER = """
UPDATE users
SET {update_fields}
WHERE id = %(user_id)s
RETURNING id, username, email, is_active, created_at;
"""

# 사용자 삭제
DELETE_USER = """
DELETE FROM users
WHERE id = %(user_id)s;
"""

# 전체 사용자 수 조회
SELECT_USER_COUNT = """
SELECT COUNT(*) as count FROM users;
"""

# 비밀번호 업데이트
UPDATE_PASSWORD = """
UPDATE users
SET hashed_password = %(hashed_password)s
WHERE id = %(user_id)s;
""" 