"""
전역 검색을 위한 검색 엔진 유틸리티
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from backend.models.user import User
from backend.models.item import Item
from backend.models.item_review import ItemReview
from backend.core.cache import cache

class SearchEngine:
    def __init__(self, db: Session):
        self.db = db
        self.entity_mappings = {
            "users": User,
            "items": Item,
            "reviews": ItemReview
        }

    def search_users(
        self,
        query: str,
        limit: int = 10,
        skip: int = 0,
        sort_by: str = "created_at",
        sort_direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """사용자 검색"""
        users = self.db.query(User).filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
                User.full_name.ilike(f"%{query}%")
            )
        ).order_by(
            func.desc(getattr(User, sort_by)) if sort_direction == "desc"
            else func.asc(getattr(User, sort_by))
        ).offset(skip).limit(limit).all()

        return [{
            "id": user.id,
            "type": "user",
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None
        } for user in users]

    def search_items(
        self,
        query: str,
        limit: int = 10,
        skip: int = 0,
        sort_by: str = "created_at",
        sort_direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """아이템 검색"""
        items = self.db.query(Item).filter(
            or_(
                Item.name.ilike(f"%{query}%"),
                Item.description.ilike(f"%{query}%")
            )
        ).order_by(
            func.desc(getattr(Item, sort_by)) if sort_direction == "desc"
            else func.asc(getattr(Item, sort_by))
        ).offset(skip).limit(limit).all()

        return [{
            "id": item.id,
            "type": "item",
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "created_at": item.created_at.isoformat() if item.created_at else None
        } for item in items]

    def search_reviews(
        self,
        query: str,
        limit: int = 10,
        skip: int = 0,
        sort_by: str = "created_at",
        sort_direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """리뷰 검색"""
        reviews = self.db.query(ItemReview).filter(
            or_(
                ItemReview.content.ilike(f"%{query}%"),
                ItemReview.title.ilike(f"%{query}%")
            )
        ).order_by(
            func.desc(getattr(ItemReview, sort_by)) if sort_direction == "desc"
            else func.asc(getattr(ItemReview, sort_by))
        ).offset(skip).limit(limit).all()

        return [{
            "id": review.id,
            "type": "review",
            "title": review.title,
            "content": review.content,
            "rating": review.rating,
            "item_id": review.item_id,
            "created_at": review.created_at.isoformat() if review.created_at else None
        } for review in reviews]

    @cache.memoize(timeout=300)
    def global_search(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 10,
        skip: int = 0,
        sort_by: str = "created_at",
        sort_direction: str = "desc"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """전역 검색"""
        results = {}
        
        # 검색할 엔티티 타입이 지정되지 않은 경우 모든 타입 검색
        if not entity_types:
            entity_types = list(self.entity_mappings.keys())

        # 각 엔티티 타입별로 검색 수행
        for entity_type in entity_types:
            if entity_type == "users":
                results["users"] = self.search_users(
                    query, limit, skip, sort_by, sort_direction
                )
            elif entity_type == "items":
                results["items"] = self.search_items(
                    query, limit, skip, sort_by, sort_direction
                )
            elif entity_type == "reviews":
                results["reviews"] = self.search_reviews(
                    query, limit, skip, sort_by, sort_direction
                )

        return results 