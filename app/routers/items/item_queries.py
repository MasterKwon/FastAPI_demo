"""
상품 관련 SQL 쿼리
"""
from typing import Dict, Any

# 상품 생성
INSERT_ITEM = """
INSERT INTO items (name, description, price, tax, created_at)
VALUES (%(name)s, %(description)s, %(price)s, %(tax)s, %(created_at)s)
RETURNING id, name, description, price, tax, created_at;
"""

# 대량 상품 생성
BULK_INSERT_ITEMS = """
INSERT INTO items (name, description, price, tax, created_at)
SELECT * FROM UNNEST(
    %(names)s::text[],
    %(descriptions)s::text[],
    %(prices)s::numeric[],
    %(taxes)s::numeric[],
    %(created_at)s::timestamptz[]
)
RETURNING id, name, description, price, tax, created_at;
"""

# 모든 상품 조회
SELECT_ALL_ITEMS = """
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
GROUP BY i.id
ORDER BY {sort_column} {sort_direction}
LIMIT %(limit)s OFFSET %(skip)s;
"""

# 전체 상품 수 조회
SELECT_ITEM_COUNT = """
SELECT COUNT(*) as count FROM items;
"""

# 상품 검색 쿼리 템플릿
SEARCH_ITEMS_TEMPLATE = """
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
{where_condition}
GROUP BY i.id
ORDER BY {sort_column} {sort_direction}
LIMIT %(limit)s OFFSET %(offset)s;
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
WHERE i.id = %(item_id)s
GROUP BY i.id;
"""

# 상품 업데이트
UPDATE_ITEM = """
UPDATE items
SET {update_fields}
WHERE id = %(item_id)s
RETURNING id, name, description, price, tax, created_at;
"""

# 상품 삭제
DELETE_ITEM = """
DELETE FROM items
WHERE id = %(item_id)s;
"""

# 이미지 관련 쿼리
class ImageQueries:
    # 이미지 추가
    INSERT = """
    INSERT INTO item_images (item_id, image_path, image_filename, original_filename, file_extension, file_size, created_at)
    VALUES (%(item_id)s, %(image_path)s, %(image_filename)s, %(original_filename)s, %(file_extension)s, %(file_size)s, %(created_at)s)
    RETURNING id, item_id, image_path, image_filename, original_filename, file_extension, file_size, created_at;
    """
    
    # 이미지 조회
    SELECT_BY_ITEM = """
    SELECT id, item_id, image_path, image_filename, original_filename, file_extension, file_size, created_at
    FROM item_images
    WHERE item_id = %(item_id)s
    ORDER BY created_at DESC;
    """
    
    # 이미지 삭제
    DELETE = """
    DELETE FROM item_images
    WHERE id = %(img_id)s
    RETURNING image_path, image_filename;
    """
    
    # 상품의 모든 이미지 삭제
    DELETE_ALL = """
    DELETE FROM item_images
    WHERE item_id = %(item_id)s
    RETURNING image_path, image_filename;
    """
    
    # 이미지 업데이트
    UPDATE = """
    UPDATE item_images 
    SET image_path = %(image_path)s,
        image_filename = %(image_filename)s,
        original_filename = %(original_filename)s,
        file_extension = %(file_extension)s,
        file_size = %(file_size)s
    WHERE item_id = %(item_id)s
    RETURNING id, created_at;
    """
    
    # 상품의 이미지 상세 정보 조회
    SELECT_IMAGE_DETAILS = """
    SELECT image_path, image_filename, original_filename, file_extension, file_size
    FROM item_images 
    WHERE item_id = %(item_id)s;
    """
    
    # 상품의 이미지 경로 조회
    SELECT_IMAGE_PATH = """
    SELECT image_path, image_filename
    FROM item_images
    WHERE id = %(img_id)s;
    """ 