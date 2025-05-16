# FastAPI Demo Project

## 프로젝트 구조
```
backend/
├── database/
│   ├── schemas/        # 데이터베이스 스키마
│   └── migrations/     # 데이터베이스 마이그레이션
├── models/            # Pydantic 모델
├── queries/           # SQL 쿼리
├── routers/           # API 라우터
├── tools/            # 유틸리티 도구
└── main.py           # 애플리케이션 진입점
```

## 개발 환경 설정

### 1. 가상환경 생성 및 활성화
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 추가합니다:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/dbname
```

### 4. 데이터베이스 설정
```bash
# 데이터베이스 생성
createdb dbname

# 스키마 적용
psql -d dbname -f backend/database/schemas/schema.sql
```

## 모델 동기화 도구

쿼리와 Pydantic 모델 간의 동기화를 자동화하는 도구가 포함되어 있습니다. 이 도구는 SQL 쿼리 파일을 분석하여 해당하는 Pydantic 모델을 자동으로 생성/업데이트합니다.

### 사용 방법

1. 모든 모델 동기화:
```bash
python backend/tools/model_sync.py
```

2. 특정 모델만 동기화:
```python
from backend.tools.model_sync import sync_model_with_query
from pathlib import Path

# 예: item_review_queries.py만 업데이트
sync_model_with_query(
    Path('backend/queries/item_review_queries.py'),
    Path('backend/models/item_review.py')
)
```

### 주요 기능

1. 쿼리 파일 분석
   - 파라미터와 결과 컬럼 정보 추출
   - 필드 타입 자동 추론
   - 테이블 이름 추출

2. 모델 자동 생성
   - Base 모델 (id와 created_at 제외)
   - Response 모델 (id와 created_at 포함)
   - 필드 설명 자동 추가

3. 지원하는 파일 매핑
   - item_queries.py → item.py
   - item_image_queries.py → item_image.py
   - item_review_queries.py → item_review.py
   - user_queries.py → user.py

### 타입 추론 규칙

- ID, 번호: `int`
- 날짜, 시간, 일시: `datetime`
- 가격, 금액, 세금, 신뢰도: `float`
- 여부, 활성화: `bool`
- 기타: `str`

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 개발 가이드라인

### 1. 코드 스타일
- [backend-style.mdc](./backend-style.mdc) 파일을 참고하여 코드 스타일을 준수합니다.

### 2. 데이터베이스
- 모든 테이블은 `id`와 `created_at` 컬럼을 포함해야 합니다.
- 외래 키는 `_id` 접미사를 사용합니다.
- 테이블 이름은 복수형을 사용합니다.

### 3. API 엔드포인트
- RESTful 규칙을 따릅니다.
- 리소스는 복수형을 사용합니다.
- HTTP 메서드는 목적에 맞게 사용합니다.

### 4. 에러 처리
- 모든 에러는 적절한 HTTP 상태 코드와 함께 반환됩니다.
- 에러 메시지는 명확하고 이해하기 쉽게 작성합니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 