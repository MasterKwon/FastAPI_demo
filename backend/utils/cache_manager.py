"""
캐시 관리 유틸리티
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.utils.logger import app_logger, LogType
import logging

class CacheManager:
    """캐시 관리 클래스"""
    
    def __init__(self):
        self.cache = {}
        self.stats = {
            "total_keys": 0,
            "last_updated": None,
            "cache_type": "memory"
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        캐시 상태를 조회합니다.
        
        Returns:
            Dict[str, Any]: 캐시 상태 정보
        """
        self.stats.update({
            "total_keys": len(self.cache),
            "last_updated": datetime.utcnow().isoformat()
        })
        return self.stats
    
    def clear_cache(self) -> bool:
        """
        캐시를 초기화합니다.
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            self.cache.clear()
            self.stats["total_keys"] = 0
            self.stats["last_updated"] = datetime.utcnow().isoformat()
            return True
        except Exception as e:
            app_logger.log(
                logging.ERROR,
                f"캐시 초기화 실패: {str(e)}",
                log_type=LogType.ALL
            )
            return False
    
    def get_cache_keys(self, pattern: str = "*") -> List[str]:
        """
        캐시 키 목록을 조회합니다.
        
        Args:
            pattern (str): 검색할 키 패턴
            
        Returns:
            List[str]: 캐시 키 목록
        """
        if pattern == "*":
            return list(self.cache.keys())
        return [key for key in self.cache.keys() if pattern in key]
    
    def delete_cache_key(self, key: str) -> bool:
        """
        특정 캐시 키를 삭제합니다.
        
        Args:
            key (str): 삭제할 캐시 키
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if key in self.cache:
                del self.cache[key]
                self.stats["total_keys"] = len(self.cache)
                self.stats["last_updated"] = datetime.utcnow().isoformat()
                return True
            return False
        except Exception as e:
            app_logger.log(
                logging.ERROR,
                f"캐시 키 삭제 실패: {str(e)}",
                log_type=LogType.ALL
            )
            return False 