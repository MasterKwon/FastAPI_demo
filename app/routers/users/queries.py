"""
사용자 관련 SQL 쿼리
"""

# 사용자 생성
INSERT_USER = """
INSERT INTO users (email, hashed_password, full_name)
VALUES (%(email)s, %(hashed_password)s, %(full_name)s)
RETURNING id, email, full_name, is_active;
"""

# 모든 사용자 조회
SELECT_ALL_USERS = """
SELECT id, email, full_name, is_active
FROM users;
"""

# 특정 사용자 조회
SELECT_USER_BY_ID = """
SELECT id, email, full_name, is_active
FROM users
WHERE id = %(user_id)s;
"""

# 이메일로 사용자 조회
SELECT_USER_BY_EMAIL = """
SELECT id, email, hashed_password, full_name, is_active
FROM users
WHERE email = %(email)s;
"""

# 사용자명으로 사용자 조회
SELECT_USER_BY_USERNAME = """
SELECT id, username, email, full_name, is_active, created_at
FROM users
WHERE username = %(username)s;
"""

# 동적 검색 쿼리 템플릿
SEARCH_USERS_TEMPLATE = """
SELECT id, username, email, full_name, is_active, created_at
FROM users
WHERE {where_clause}
ORDER BY created_at DESC
LIMIT %(limit)s OFFSET %(offset)s;
""" 