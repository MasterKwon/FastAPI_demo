"""
상품 리뷰 관련 SQL 쿼리

파라미터:
    $1: id (리뷰 ID)
    $2: item_id (상품 ID)
    $3: usr_id (사용자 ID)
    $4: review_content (리뷰 내용)
    $5: score (평점, 1-5)
    $6: sentiment (감성 분석 결과)
    $7: confidence (감성 분석 신뢰도)
    $8: explanation (감성 분석 설명)
    $9: created_at (생성일시)

결과 컬럼:
    id: 리뷰 ID
    item_id: 상품 ID
    usr_id: 사용자 ID
    review_content: 리뷰 내용
    score: 평점
    sentiment: 감성 분석 결과
    confidence: 감성 분석 신뢰도
    explanation: 감성 분석 설명
    created_at: 생성일시
    username: 리뷰 작성자 이름
    item_name: 상품명
    total_count: 전체 리뷰 수
"""
from typing import Dict, Any

# 리뷰 생성
INSERT_ITEM_REVIEW = """
INSERT INTO item_review (item_id, usr_id, review_content, score, sentiment, confidence, explanation, created_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
RETURNING id, item_id, usr_id, review_content, score, sentiment, confidence, explanation, created_at;
"""

# 특정 리뷰 조회
SELECT_ITEM_REVIEW_BY_ID = """
SELECT r.id, r.item_id, r.usr_id, r.review_content, r.score, r.sentiment, r.confidence, r.explanation, r.created_at,
       u.username, i.name as item_name
FROM item_review r
JOIN users u ON r.usr_id = u.id
JOIN items i ON r.item_id = i.id
WHERE r.id = $1;
"""

# 리뷰 업데이트
UPDATE_ITEM_REVIEW = """
UPDATE item_review
SET review_content = COALESCE($2, review_content),
    score = COALESCE($3, score),
    sentiment = COALESCE($4, sentiment),
    confidence = COALESCE($5, confidence),
    explanation = COALESCE($6, explanation)
WHERE id = $1
RETURNING id, item_id, usr_id, review_content, score, sentiment, confidence, explanation, created_at;
"""

# 리뷰 삭제
DELETE_ITEM_REVIEW = """
DELETE FROM item_review
WHERE id = $1;
"""

# 리뷰 검색 쿼리 템플릿
SELECT_ITEM_REVIEWS_TEMPLATE = """
WITH review_counts AS (
    SELECT COUNT(*) as total_count
    FROM item_review r
    JOIN users u ON r.usr_id = u.id
    JOIN items i ON r.item_id = i.id
    {where_condition}
)
SELECT r.id, r.item_id, r.usr_id, r.review_content, r.score, r.sentiment, r.confidence, r.explanation, r.created_at,
       u.username, i.name as item_name,
       (SELECT total_count FROM review_counts) as total_count
FROM item_review r
JOIN users u ON r.usr_id = u.id
JOIN items i ON r.item_id = i.id
{where_condition}
ORDER BY {sort_column} {sort_direction}
LIMIT $1 OFFSET $2;
"""

# 전체 리뷰 수 조회
SELECT_ITEM_REVIEW_COUNT = """
SELECT COUNT(*) as count FROM item_review;
"""

# 상품별 리뷰 수 조회
SELECT_ITEM_REVIEW_COUNT_BY_ITEM = """
SELECT COUNT(*) as count FROM item_review WHERE item_id = $1;
"""

# 사용자별 리뷰 수 조회
SELECT_ITEM_REVIEW_COUNT_BY_USER = """
SELECT COUNT(*) as count FROM item_review WHERE usr_id = $1;
""" 