-- 마이그레이션 버전: 001
-- 설명: 초기 데이터베이스 스키마 생성

-- 트랜잭션 시작
BEGIN;

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

-- 아이템 테이블 생성
CREATE TABLE IF NOT EXISTS items (
    id SERIAL NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    tax DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT items_pk PRIMARY KEY (id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS items_idx01 ON items(name);
CREATE INDEX IF NOT EXISTS items_idx02 ON items(description);
CREATE INDEX IF NOT EXISTS items_idx03 ON items(created_at);

-- 코멘트 추가
COMMENT ON TABLE items IS '상품 정보를 저장하는 테이블';
COMMENT ON COLUMN items.id IS '상품 고유 ID';
COMMENT ON COLUMN items.name IS '상품명';
COMMENT ON COLUMN items.description IS '상품 설명';
COMMENT ON COLUMN items.price IS '상품 가격';
COMMENT ON COLUMN items.tax IS '상품 세금';
COMMENT ON COLUMN items.created_at IS '상품 등록일시';


-- 아이템 이미지 테이블 생성
CREATE TABLE IF NOT EXISTS item_images (
    id serial NOT NULL,
	item_id int NULL,
	image_path varchar(255) NOT NULL,
	image_filename varchar(255) NOT NULL,
	original_filename varchar(255) NOT NULL,
	file_extension varchar(10) NOT NULL,
	file_size int NOT NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
    CONSTRAINT item_images_pk PRIMARY KEY (id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS item_images_idx01 ON item_images(item_id);

COMMENT ON TABLE item_images IS '상품 이미지 정보를 저장하는 테이블';
COMMENT ON COLUMN item_images.id IS '이미지 고유 ID';
COMMENT ON COLUMN item_images.item_id IS '상품 ID';
COMMENT ON COLUMN item_images.image_path IS '이미지 저장 경로';
COMMENT ON COLUMN item_images.image_filename IS '이미지 파일명';
COMMENT ON COLUMN item_images.original_filename IS '원본 파일명';
COMMENT ON COLUMN item_images.file_extension IS '파일 확장자';
COMMENT ON COLUMN item_images.file_size IS '파일 크기';
COMMENT ON COLUMN item_images.created_at IS '이미지 등록일시'; 

-- 트랜잭션 커밋
COMMIT; 