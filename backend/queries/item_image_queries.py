"""
상품 이미지 관련 SQL 쿼리

파라미터 설명:
$1: id (이미지 ID)
$2: item_id (상품 ID)
$3: image_path (이미지 경로)
$4: image_filename (이미지 파일명)
$5: original_filename (원본 파일명)
$6: file_extension (파일 확장자)
$7: file_size (파일 크기)
$8: created_at (생성일시)

결과 컬럼 설명:
id: 이미지 ID
item_id: 상품 ID
image_path: 이미지 경로
image_filename: 이미지 파일명
original_filename: 원본 파일명
file_extension: 파일 확장자
file_size: 파일 크기
created_at: 생성일시
"""
from typing import Dict, Any

# 이미지 추가
INSERT_IMAGE = """
INSERT INTO item_images (item_id, image_path, image_filename, original_filename, file_extension, file_size, created_at)
VALUES ($1, $2, $3, $4, $5, $6, $7)
RETURNING id, item_id, image_path, image_filename, original_filename, file_extension, file_size, created_at;
"""

# 이미지 업데이트
UPDATE_IMAGE = """
UPDATE item_images 
SET image_path = $2,
    image_filename = $3,
    original_filename = $4,
    file_extension = $5,
    file_size = $6
WHERE item_id = $1
RETURNING id, created_at;
"""

# 이미지 삭제
DELETE_IMAGE = """
DELETE FROM item_images
WHERE id = $1
RETURNING image_path, image_filename;
"""

# 이미지 조회
SELECT_IMAGES_BY_ITEM = """
SELECT id, item_id, image_path, image_filename, original_filename, file_extension, file_size, created_at
FROM item_images
WHERE item_id = $1
ORDER BY created_at DESC;
"""

# 상품의 모든 이미지 삭제
DELETE_ALL_IMAGES = """
DELETE FROM item_images
WHERE item_id = $1
RETURNING image_path, image_filename;
""" 