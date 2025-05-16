"""
상품 관련 서비스
"""
from datetime import datetime
import logging
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from backend.models.item import ItemCreate, ItemResponse, ItemImage
from backend.utils.logger import app_logger, LogType
from backend.database.exceptions import DatabaseError
from backend.utils.file_handler import save_file, delete_file, FileType
from backend.queries.item_queries import (
    INSERT_ITEM, SELECT_ITEM_BY_ID, SELECT_ITEMS,
    UPDATE_ITEM, DELETE_ITEM, INSERT_ITEM_IMAGE,
    SELECT_ITEM_IMAGE, DELETE_ITEM_IMAGE
)
import os

class ItemService:
    def __init__(self, db: psycopg2.extensions.connection):
        self.db = db
        self.logger = logging.getLogger(__name__)

    async def create_item(self, item: ItemCreate) -> Dict[str, Any]:
        """새로운 상품을 생성합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # 상품 정보 저장
                cursor.execute(
                    INSERT_ITEM,
                    {
                        "name": item.name,
                        "description": item.description,
                        "price": item.price,
                        "tax": item.tax,
                        "created_at": datetime.now()
                    }
                )
                result = cursor.fetchone()
                self.db.commit()
                
                app_logger.log(
                    logging.INFO,
                    f"상품 생성 성공: {result['id']}",
                    log_type=LogType.ALL
                )
                
                return result
                
        except Exception as e:
            self.db.rollback()
            app_logger.log(
                logging.ERROR,
                f"상품 생성 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"상품 생성 실패: {str(e)}")

    async def get_items(
        self,
        skip: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_direction: str = "desc"
    ) -> Dict[str, Any]:
        """상품 목록을 조회합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # 상품 목록 조회
                query = SELECT_ITEMS.format(
                    sort_column=sort_by,
                    sort_direction=sort_direction
                )
                
                cursor.execute(query, {"limit": limit, "offset": skip})
                items = cursor.fetchall()
                
                # 첫 번째 레코드에서 total_count 추출
                total = items[0]["total_count"] if items else 0
                
                # total_count 필드 제거
                for item in items:
                    item.pop("total_count", None)
                
                return {
                    "items": items,
                    "total": total,
                    "skip": skip,
                    "limit": limit
                }
                
        except Exception as e:
            app_logger.log(
                logging.ERROR,
                f"상품 목록 조회 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"상품 목록 조회 실패: {str(e)}")

    async def get_item(self, item_id: int) -> Dict[str, Any]:
        """특정 상품을 조회합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(SELECT_ITEM_BY_ID, {"item_id": item_id})
                result = cursor.fetchone()
                if not result:
                    raise ValueError("상품을 찾을 수 없습니다.")
                
                return result
                
        except Exception as e:
            app_logger.log(
                logging.ERROR,
                f"상품 조회 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"상품 조회 실패: {str(e)}")

    async def update_item(self, item_id: int, item: ItemCreate) -> Dict[str, Any]:
        """상품 정보를 업데이트합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # 상품 존재 여부 확인
                cursor.execute(SELECT_ITEM_BY_ID, {"item_id": item_id})
                existing_item = cursor.fetchone()
                if not existing_item:
                    raise ValueError("상품을 찾을 수 없습니다.")
                
                # 상품 정보 업데이트
                cursor.execute(
                    UPDATE_ITEM,
                    {
                        "item_id": item_id,
                        "name": item.name,
                        "description": item.description,
                        "price": item.price,
                        "tax": item.tax,
                        "updated_at": datetime.now()
                    }
                )
                result = cursor.fetchone()
                
                self.db.commit()
                
                app_logger.log(
                    logging.INFO,
                    f"상품 정보 업데이트 성공: {item_id}",
                    log_type=LogType.ALL
                )
                
                return result
                
        except Exception as e:
            self.db.rollback()
            app_logger.log(
                logging.ERROR,
                f"상품 정보 업데이트 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"상품 정보 업데이트 실패: {str(e)}")

    async def delete_item(self, item_id: int) -> None:
        """상품을 삭제합니다."""
        try:
            with self.db.cursor() as cursor:
                # 상품 존재 여부 확인
                cursor.execute(SELECT_ITEM_BY_ID, {"item_id": item_id})
                if not cursor.fetchone():
                    raise ValueError("상품을 찾을 수 없습니다.")
                
                # 상품 삭제
                cursor.execute(DELETE_ITEM, {"item_id": item_id})
                
                self.db.commit()
                
                app_logger.log(
                    logging.INFO,
                    f"상품 삭제 성공: {item_id}",
                    log_type=LogType.ALL
                )
                
        except Exception as e:
            self.db.rollback()
            app_logger.log(
                logging.ERROR,
                f"상품 삭제 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"상품 삭제 실패: {str(e)}")

    async def add_item_image(self, item_id: int, image: Any) -> Dict[str, Any]:
        """상품에 이미지를 추가합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # 상품 존재 여부 확인
                cursor.execute(SELECT_ITEM_BY_ID, {"item_id": item_id})
                if not cursor.fetchone():
                    raise ValueError("상품을 찾을 수 없습니다.")
                
                # 이미지 저장 및 상세 정보 추출
                file_info = await save_file(image, FileType.IMAGE)
                original_filename = image.filename
                file_extension = os.path.splitext(image.filename)[1] if image.filename else '.jpg'
                file_size = image.size or 0
                
                # 이미지 정보 저장
                cursor.execute(
                    INSERT_ITEM_IMAGE,
                    {
                        "item_id": item_id,
                        "image_path": file_info["path"],
                        "image_filename": file_info["filename"],
                        "original_filename": original_filename,
                        "file_extension": file_extension,
                        "file_size": file_size,
                        "created_at": datetime.now()
                    }
                )
                result = cursor.fetchone()
                
                self.db.commit()
                
                app_logger.log(
                    logging.INFO,
                    f"상품 이미지 추가 성공: {result['id']}",
                    log_type=LogType.ALL
                )
                
                return result
                
        except Exception as e:
            self.db.rollback()
            app_logger.log(
                logging.ERROR,
                f"상품 이미지 추가 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"상품 이미지 추가 실패: {str(e)}")

    async def delete_item_image(self, item_id: int, img_id: int) -> None:
        """상품의 특정 이미지를 삭제합니다."""
        try:
            with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
                # 이미지 정보 조회
                cursor.execute(
                    SELECT_ITEM_IMAGE,
                    {"img_id": img_id, "item_id": item_id}
                )
                result = cursor.fetchone()
                if not result:
                    raise ValueError("이미지를 찾을 수 없습니다.")
                
                # 이미지 파일 삭제
                delete_file({
                    "path": result["image_path"],
                    "filename": result["image_filename"]
                })
                
                # 이미지 정보 삭제
                cursor.execute(DELETE_ITEM_IMAGE, {"img_id": img_id})
                
                self.db.commit()
                
                app_logger.log(
                    logging.INFO,
                    f"상품 이미지 삭제 성공: {img_id}",
                    log_type=LogType.ALL
                )
                
        except Exception as e:
            self.db.rollback()
            app_logger.log(
                logging.ERROR,
                f"상품 이미지 삭제 실패: {str(e)}",
                log_type=LogType.ALL
            )
            raise DatabaseError(f"상품 이미지 삭제 실패: {str(e)}") 