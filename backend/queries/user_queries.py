"""
사용자 관련 SQL 쿼리

파라미터 설명:
$1: id (사용자 ID)
$2: username (사용자명)
$3: email (이메일)
$4: hashed_password (해시된 비밀번호)
$5: is_active (활성화 여부)
$6: created_at (생성일시)

결과 컬럼 설명:
id: 사용자 ID
username: 사용자명
email: 이메일
is_active: 활성화 여부
created_at: 생성일시
hashed_password: 해시된 비밀번호 (로그인 시에만 반환)
total_count: 전체 사용자 수
"""
from typing import Dict, Any

# 사용자 생성
INSERT_USER = """
INSERT INTO users (username, email, hashed_password, is_active, created_at)
VALUES ($1, $2, $3, $4, $5)
RETURNING id, username, email, is_active, created_at;
"""

# 특정 사용자 조회
SELECT_USER_BY_ID = """
SELECT id, username, email, is_active, created_at
FROM users
WHERE id = $1;
"""

# 사용자 업데이트
UPDATE_USER = """
UPDATE users
SET username = COALESCE($2, username),
    email = COALESCE($3, email),
    is_active = COALESCE($4, is_active)
WHERE id = $1
RETURNING id, username, email, is_active, created_at;
"""

# 사용자 삭제
DELETE_USER = """
DELETE FROM users
WHERE id = $1;
"""

# 사용자 검색 쿼리 템플릿
SELECT_USERS_TEMPLATE = """
WITH user_counts AS (
    SELECT COUNT(*) as total_count
    FROM users
    {where_condition}
)
SELECT id, username, email, is_active, created_at,
       (SELECT total_count FROM user_counts) as total_count
FROM users
{where_condition}
ORDER BY {sort_column} {sort_direction}
LIMIT $1 OFFSET $2;
"""

# 전체 사용자 수 조회
SELECT_USER_COUNT = """
SELECT COUNT(*) as count FROM users;
"""

# 이메일로 사용자 조회
SELECT_USER_BY_EMAIL = """
SELECT id, username, email, is_active, created_at
FROM users
WHERE email = $1;
"""

# 사용자명으로 사용자 조회
SELECT_USER_BY_USERNAME = """
SELECT id, username, email, is_active, created_at
FROM users
WHERE username = $1;
"""

# 로그인을 위한 사용자 조회
SELECT_USER_FOR_LOGIN = """
SELECT id, username, email, hashed_password, is_active, created_at
FROM users
WHERE email = $1;
"""

# 비밀번호 업데이트
UPDATE_PASSWORD = """
UPDATE users
SET hashed_password = $2
WHERE id = $1;
""" 