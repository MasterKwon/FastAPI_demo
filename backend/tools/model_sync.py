"""
쿼리와 모델 간의 동기화를 위한 도구

이 스크립트는 SQL 쿼리 파일을 분석하여 해당하는 Pydantic 모델을 자동으로 생성/업데이트합니다.

사용법:
1. 쿼리 파일 작성 시 다음 형식으로 주석을 추가:
   - 파라미터: $1: param_name (설명)
   - 결과 컬럼: column_name: 타입 (설명)

예시:
```sql
-- $1: user_id (사용자 ID)
-- $2: item_id (상품 ID)
-- id: int (리뷰 ID)
-- content: str (리뷰 내용)
-- rating: float (평점)
-- created_at: datetime (작성일시)
SELECT * FROM item_reviews WHERE user_id = $1 AND item_id = $2;
```

2. 스크립트 실행:
   ```bash
   python -m backend.tools.model_sync
   ```

3. 결과:
   - queries/ 디렉토리의 쿼리 파일을 분석
   - schemas/ 디렉토리에 해당하는 Pydantic 모델 자동 생성
   - 기존 모델 파일이 있다면 업데이트

주의사항:
- 쿼리 파일의 주석 형식을 정확히 지켜야 함
- 테이블 이름은 쿼리에서 자동으로 추론됨
- 모델 이름은 테이블 이름을 기반으로 자동 생성됨
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def parse_query_file(file_path: Path) -> Dict:
    """쿼리 파일을 파싱하여 모델 정보를 추출합니다."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 파일 설명에서 파라미터와 결과 컬럼 정보 추출
    param_pattern = r'\$(\d+):\s*(\w+)\s*\(([^)]+)\)'
    result_pattern = r'(\w+):\s*([^(]+)(?:\(([^)]+)\))?'

    params = {}
    results = {}
    
    # 파라미터 파싱
    for match in re.finditer(param_pattern, content):
        param_num, param_name, param_desc = match.groups()
        params[param_name] = {
            'type': infer_type(param_desc),
            'description': param_desc
        }

    # 결과 컬럼 파싱
    for match in re.finditer(result_pattern, content):
        col_name, col_type, col_desc = match.groups()
        if col_desc is None:
            col_desc = col_type.strip()
        results[col_name] = {
            'type': infer_type(col_type),
            'description': col_desc
        }

    return {
        'params': params,
        'results': results,
        'table_name': infer_table_name(content)
    }

def infer_type(description: str) -> str:
    """설명을 기반으로 Python 타입을 추론합니다."""
    description = description.lower()
    if any(word in description for word in ['id', '번호']):
        return 'int'
    elif any(word in description for word in ['날짜', '시간', '일시']):
        return 'datetime'
    elif any(word in description for word in ['가격', '금액', '세금', '신뢰도']):
        return 'float'
    elif any(word in description for word in ['여부', '활성화']):
        return 'bool'
    else:
        return 'str'

def infer_table_name(content: str) -> str:
    """쿼리 내용에서 테이블 이름을 추론합니다."""
    # INSERT 문에서 테이블 이름 추출
    insert_match = re.search(r'INSERT INTO (\w+)', content)
    if insert_match:
        return insert_match.group(1)
    
    # SELECT 문에서 테이블 이름 추출
    select_match = re.search(r'FROM (\w+)', content)
    if select_match:
        return select_match.group(1)
    
    return None

def generate_model_code(table_info: Dict) -> str:
    """테이블 정보를 기반으로 Pydantic 모델 코드를 생성합니다."""
    table_name = table_info['table_name']
    results = table_info['results']
    
    # 모델 이름 생성 (테이블 이름을 단수형으로 변환)
    model_name = ''.join(word.capitalize() for word in table_name.split('_'))
    if model_name.endswith('s'):
        model_name = model_name[:-1]
    
    # 기본 모델 코드 생성
    code = f'''"""
{table_name} 테이블의 Pydantic 모델
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class {model_name}Base(BaseModel):
    """
    {table_name} 테이블의 기본 모델
    """
'''
    
    # 필드 추가
    for field_name, field_info in results.items():
        if field_name != 'id':  # id는 기본 모델에서 제외
            field_type = field_info['type']
            if field_type == 'datetime':
                field_type = 'datetime'
            code += f"    {field_name}: {field_type} = Field(description='{field_info['description']}')\n"
    
    # Response 모델 추가
    code += f'''
class {model_name}Response({model_name}Base):
    """
    {table_name} 테이블의 응답 모델
    """
    id: int = Field(description='{table_name} ID')
    created_at: datetime = Field(description='생성일시')
    
    model_config = ConfigDict(from_attributes=True)
'''
    
    return code

def sync_model_with_query(query_file: Path, schema_file: Path):
    """쿼리 파일을 기반으로 스키마 파일을 동기화합니다."""
    # 쿼리 파일 파싱
    table_info = parse_query_file(query_file)
    
    # 모델 코드 생성
    model_code = generate_model_code(table_info)
    
    # 스키마 파일 업데이트
    with open(schema_file, 'w', encoding='utf-8') as f:
        f.write(model_code)

def main():
    """메인 함수"""
    # 쿼리 파일과 스키마 파일 매핑
    file_mappings = {
        'item_queries.py': 'item.py',
        'item_review_queries.py': 'item_review.py',
        'user_queries.py': 'user.py'
    }
    
    base_dir = Path(__file__).parent.parent
    queries_dir = base_dir / 'queries'
    schemas_dir = base_dir / 'schemas'
    
    for query_file, schema_file in file_mappings.items():
        query_path = queries_dir / query_file
        schema_path = schemas_dir / schema_file
        
        if query_path.exists():
            print(f"Syncing {query_file} with {schema_file}...")
            sync_model_with_query(query_path, schema_path)
            print(f"Done syncing {schema_file}")

if __name__ == '__main__':
    main() 