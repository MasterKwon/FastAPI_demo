"""
대량 업로드 관련 서비스
"""
import pandas as pd
from typing import List, Dict, Tuple
import logging
from io import BytesIO
from backend.models.items import ItemCreate
from backend.utils.logger import app_logger, LogType

logger = logging.getLogger(__name__)

class ExcelValidationError(Exception):
    """엑셀 유효성 검증 실패 예외"""
    def __init__(self, message: str, errors: List[Dict[str, str]]):
        self.message = message
        self.errors = errors
        super().__init__(self.message)

def validate_excel_data(df: pd.DataFrame) -> Tuple[List[ItemCreate], List[Dict[str, str]]]:
    """
    엑셀 데이터 유효성 검증
    
    Args:
        df: 검증할 데이터프레임
        
    Returns:
        Tuple[List[ItemCreate], List[Dict[str, str]]]: 
            - 유효한 아이템 목록
            - 오류 목록
    """
    required_columns = ['name', 'price']
    optional_columns = ['description', 'tax']
    
    # 필수 컬럼 확인
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ExcelValidationError(
            "필수 컬럼이 누락되었습니다",
            [{"error": f"누락된 컬럼: {', '.join(missing_columns)}"}]
        )
    
    valid_items = []
    errors = []
    
    for idx, row in df.iterrows():
        row_number = idx + 2  # 엑셀의 실제 행 번호 (헤더 제외)
        try:
            # 필수 필드 검증
            if pd.isna(row['name']) or str(row['name']).strip() == '':
                errors.append({
                    "row": row_number,
                    "error": "name 필드는 필수입니다"
                })
                continue
                
            if pd.isna(row['price']):
                errors.append({
                    "row": row_number,
                    "error": "price 필드는 필수입니다"
                })
                continue
            
            # 데이터 타입 검증
            try:
                price = float(row['price'])
                if price < 0:
                    errors.append({
                        "row": row_number,
                        "error": "price는 0 이상이어야 합니다"
                    })
                    continue
            except (ValueError, TypeError):
                errors.append({
                    "row": row_number,
                    "error": "price는 숫자여야 합니다"
                })
                continue
            
            # tax 필드 검증 (선택적)
            tax = None
            if 'tax' in df.columns and not pd.isna(row['tax']):
                try:
                    tax = float(row['tax'])
                    if tax < 0:
                        errors.append({
                            "row": row_number,
                            "error": "tax는 0 이상이어야 합니다"
                        })
                        continue
                except (ValueError, TypeError):
                    errors.append({
                        "row": row_number,
                        "error": "tax는 숫자여야 합니다"
                    })
                    continue
            
            # ItemCreate 모델 생성
            item = ItemCreate(
                name=str(row['name']).strip(),
                description=str(row['description']).strip() if 'description' in df.columns and not pd.isna(row['description']) else None,
                price=price,
                tax=tax
            )
            valid_items.append(item)
            
        except Exception as e:
            app_logger.log(
                logging.ERROR,
                f"Row {row_number} 처리 중 오류 발생: {str(e)}",
                log_type=LogType.ALL
            )
            errors.append({
                "row": row_number,
                "error": f"데이터 처리 중 오류 발생: {str(e)}"
            })
    
    return valid_items, errors 