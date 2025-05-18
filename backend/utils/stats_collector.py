"""
시스템 통계를 수집하는 유틸리티
"""
from typing import Dict, Any
from datetime import datetime
from backend.database.async_pool import get_async_db
from backend.utils.logger import app_logger, LogType
import logging

class StatsCollector:
    def __init__(self, db):
        self.db = db

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        시스템 통계를 수집합니다.
        
        Returns:
            Dict[str, Any]: 시스템 통계 정보
        """
        try:
            # 전체 사용자 수
            total_users = await self.db.fetchval("SELECT COUNT(*) FROM users")
            
            # 전체 아이템 수
            total_items = await self.db.fetchval("SELECT COUNT(*) FROM items")
            
            # 전체 리뷰 수
            total_reviews = await self.db.fetchval("SELECT COUNT(*) FROM item_reviews")
            
            # 활성 사용자 수
            active_users = await self.db.fetchval("SELECT COUNT(*) FROM users WHERE is_active = true")
            
            # 활성 아이템 수
            active_items = await self.db.fetchval("SELECT COUNT(*) FROM items WHERE is_active = true")
            
            # 활성 리뷰 수
            active_reviews = await self.db.fetchval("SELECT COUNT(*) FROM item_reviews WHERE is_active = true")
            
            return {
                "total_users": total_users,
                "total_items": total_items,
                "total_reviews": total_reviews,
                "active_users": active_users,
                "active_items": active_items,
                "active_reviews": active_reviews,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            app_logger.log(
                logging.ERROR,
                f"시스템 통계 수집 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise 