# 데이터베이스 스키마 문서

## 테이블 구조

### users (사용자 테이블)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | SERIAL | PRIMARY KEY | 사용자 고유 ID |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 사용자명 |
| email | VARCHAR(100) | NOT NULL, UNIQUE | 이메일 주소 |
| hashed_password | VARCHAR(255) | NOT NULL | 해시된 비밀번호 |
| is_active | BOOLEAN | DEFAULT TRUE | 계정 활성화 여부 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | 계정 생성일시 |

### items (상품 테이블)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | SERIAL | PRIMARY KEY | 상품 고유 ID |
| name | VARCHAR(100) | NOT NULL | 상품명 |
| description | TEXT | NULL | 상품 설명 |
| price | DECIMAL(10, 2) | NOT NULL | 상품 가격 |
| tax | DECIMAL(10, 2) | DEFAULT 0 | 상품 세금 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | 상품 등록일시 |

### item_images (상품 이미지 테이블)
| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | SERIAL | PRIMARY KEY | 이미지 고유 ID |
| item_id | INTEGER | NULL | 상품 ID |
| image_path | VARCHAR(255) | NOT NULL | 이미지 저장 경로 |
| image_filename | VARCHAR(255) | NOT NULL | 이미지 파일명 |
| original_filename | VARCHAR(255) | NOT NULL | 원본 파일명 |
| file_extension | VARCHAR(10) | NOT NULL | 파일 확장자 |
| file_size | INTEGER | NOT NULL | 파일 크기 |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT CURRENT_TIMESTAMP | 이미지 등록일시 |

## 인덱스

### users 테이블
- users_idx01: email 컬럼에 대한 인덱스
- users_idx02: username 컬럼에 대한 인덱스
- users_idx03: created_at 컬럼에 대한 인덱스

### items 테이블
- items_idx01: name 컬럼에 대한 인덱스
- items_idx02: description 컬럼에 대한 인덱스
- items_idx03: created_at 컬럼에 대한 인덱스

### item_images 테이블
- item_images_idx01: item_id 컬럼에 대한 인덱스

## 외래 키 관계
- item_images.item_id -> items.id

## 테이블 코멘트
- users: 사용자 정보를 저장하는 테이블
- items: 상품 정보를 저장하는 테이블
- item_images: 상품 이미지 정보를 저장하는 테이블 