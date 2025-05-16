import pytest
import pandas as pd
from backend.services.bulk_upload import validate_excel_data, ExcelValidationError
from backend.models.items import ItemCreate

def test_validate_excel_data_valid():
    """유효한 엑셀 데이터 처리 테스트"""
    # 테스트용 데이터프레임 생성
    df = pd.DataFrame({
        'name': ['상품1', '상품2', '상품3'],
        'price': [1000, 2000, 3000],
        'description': ['설명1', '설명2', '설명3'],
        'tax': [0.1, 0.1, 0.1]
    })
    
    # 데이터 검증
    valid_items, errors = validate_excel_data(df)
    
    # 결과 검증
    assert len(valid_items) == 3
    assert len(errors) == 0
    
    assert valid_items[0].name == '상품1'
    assert valid_items[0].price == 1000
    assert valid_items[0].description == '설명1'
    assert valid_items[0].tax == 0.1

def test_validate_excel_data_empty():
    """빈 엑셀 데이터 처리 테스트"""
    df = pd.DataFrame(columns=['name', 'price'])
    valid_items, errors = validate_excel_data(df)
    assert len(valid_items) == 0
    assert len(errors) == 0

def test_validate_excel_data_invalid():
    """잘못된 형식의 엑셀 데이터 처리 테스트"""
    df = pd.DataFrame({
        'name': ['상품1', '상품2'],
        'price': ['invalid', -1000]  # 잘못된 가격 데이터
    })
    
    valid_items, errors = validate_excel_data(df)
    assert len(valid_items) == 0
    assert len(errors) == 2
    assert any('price는 숫자여야 합니다' in error['error'] for error in errors)
    assert any('price는 0 이상이어야 합니다' in error['error'] for error in errors)

def test_validate_excel_data_missing_columns():
    """필수 컬럼 누락 테스트"""
    df = pd.DataFrame({
        'name': ['상품1', '상품2']
    })
    
    with pytest.raises(ExcelValidationError) as exc_info:
        validate_excel_data(df)
    
    assert '필수 컬럼이 누락되었습니다' in str(exc_info.value) 