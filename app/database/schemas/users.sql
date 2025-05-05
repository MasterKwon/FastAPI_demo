-- 사용자 테이블 생성
CREATE TABLE IF NOT EXISTS users (
    id SERIAL NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_pk PRIMARY KEY (id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS users_idx01 ON users(email);
CREATE INDEX IF NOT EXISTS users_idx02 ON users(username);
CREATE INDEX IF NOT EXISTS users_idx03 ON users(created_at);

-- 코멘트 추가
COMMENT ON TABLE users IS '사용자 정보를 저장하는 테이블';
COMMENT ON COLUMN users.id IS '사용자 고유 ID';
COMMENT ON COLUMN users.username IS '사용자명';
COMMENT ON COLUMN users.email IS '이메일 주소';
COMMENT ON COLUMN users.hashed_password IS '해시된 비밀번호';
COMMENT ON COLUMN users.is_active IS '계정 활성화 여부';
COMMENT ON COLUMN users.created_at IS '계정 생성일시'; 