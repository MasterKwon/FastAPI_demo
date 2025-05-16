"""
상품 관련 SQL 쿼리

파라미터 설명:
$1: id (상품 ID)
$2: name (상품명)
$3: description (상품 설명)
$4: price (가격)
$5: tax (세금)
$6: created_at (생성일시)

결과 컬럼 설명:
id: 상품 ID
name: 상품명
description: 상품 설명
price: 가격
tax: 세금
created_at: 생성일시
images: 상품 이미지 목록 (JSON 배열)
total_count: 전체 상품 수
"""
from typing import Dict, Any

# 상품 생성
INSERT_ITEM = """
INSERT INTO items (name, description, price, tax, created_at)
VALUES ($1, $2, $3, $4, $5)
RETURNING id, name, description, price, tax, created_at;
"""

# 특정 상품 조회
SELECT_ITEM_BY_ID = """
SELECT i.id, i.name, i.description, i.price, i.tax, i.created_at,
       COALESCE(json_agg(
           json_build_object(
               'id', img.id,
               'item_id', img.item_id,
               'image_path', img.image_path,
               'image_filename', img.image_filename,
               'original_filename', img.original_filename,
               'file_extension', img.file_extension,
               'file_size', img.file_size,
               'created_at', img.created_at
           )
       ) FILTER (WHERE img.id IS NOT NULL), '[]') as images
FROM items i
LEFT JOIN item_images img ON i.id = img.item_id
WHERE i.id = $1
GROUP BY i.id;
"""

# 상품 업데이트
UPDATE_ITEM = """
UPDATE items
SET name = COALESCE($2, name),
    description = COALESCE($3, description),
    price = COALESCE($4, price),
    tax = COALESCE($5, tax)
WHERE id = $1
RETURNING id, name, description, price, tax, created_at;
"""

# 상품 삭제
DELETE_ITEM = """
DELETE FROM items
WHERE id = $1;
"""

# 상품 검색 쿼리 템플릿
SELECT_ITEMS_TEMPLATE = """
WITH item_counts AS (
    SELECT COUNT(*) as total_count
    FROM items i
    LEFT JOIN item_images img ON i.id = img.item_id
    {where_condition}
)
SELECT i.id, i.name, i.description, i.price, i.tax, i.created_at,
       COALESCE(json_agg(
           json_build_object(
               'id', img.id,
               'item_id', img.item_id,
               'image_path', img.image_path,
               'image_filename', img.image_filename,
               'original_filename', img.original_filename,
               'file_extension', img.file_extension,
               'file_size', img.file_size,
               'created_at', img.created_at
           )
       ) FILTER (WHERE img.id IS NOT NULL), '[]') as images,
       (SELECT total_count FROM item_counts) as total_count
FROM items i
LEFT JOIN item_images img ON i.id = img.item_id
{where_condition}
GROUP BY i.id
ORDER BY {sort_column} {sort_direction}
LIMIT $1 OFFSET $2;
"""

# 대량 상품 생성
BULK_INSERT_ITEMS = """
INSERT INTO items (name, description, price, tax, created_at)
SELECT * FROM UNNEST(
    $1::text[],
    $2::text[],
    $3::numeric[],
    $4::numeric[],
    $5::timestamptz[]
)
RETURNING id, name, description, price, tax, created_at;
""" 