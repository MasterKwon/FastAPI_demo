"""
아이템 관련 SQL 쿼리
"""

# 아이템 생성
INSERT_ITEM = """
INSERT INTO items (name, description, price, tax)
VALUES (%(name)s, %(description)s, %(price)s, %(tax)s)
RETURNING id, name, description, price, tax;
"""

# 모든 아이템 조회
SELECT_ALL_ITEMS = """
SELECT id, name, description, price, tax
FROM items;
"""

# 특정 아이템 조회
SELECT_ITEM_BY_ID = """
SELECT id, name, description, price, tax
FROM items
WHERE id = %(item_id)s;
""" 