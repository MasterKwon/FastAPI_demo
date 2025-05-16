# Backend

## 프로젝트 구조
```
backend/
├── routers/          # API 라우터
├── services/         # 비즈니스 로직
├── models/          # 데이터 모델
├── schemas/         # API 스키마
├── database/        # 데이터베이스 관련
├── utils/           # 유틸리티 함수
├── queries/         # SQL 쿼리
└── middleware/      # 미들웨어 (인증, 로깅, CORS 등)
```

## 코딩 컨벤션

### 1. 파일 구조
- 각 기능별로 디렉토리를 분리하지 않고 파일명으로 구분
- 예: `user_router.py`, `item_router.py`

### 2. 네이밍 규칙
- 파일명: snake_case
- 클래스명: PascalCase
- 함수/변수명: snake_case
- 상수: UPPER_SNAKE_CASE

### 3. 주석 규칙
- 모든 파일 상단에 파일 설명 주석 추가
- 모든 함수에 docstring 추가
- 복잡한 로직에 인라인 주석 추가

### 4. 에러 처리
- 모든 에러는 `DatabaseError`로 래핑
- 에러 메시지는 한글로 작성
- 로깅은 `app_logger` 사용

### 5. 쿼리 관리 규칙
- 모든 SQL 쿼리는 `queries` 디렉토리에서 관리
- 쿼리 파일은 기능별로 분리 (예: `user_queries.py`, `item_queries.py`)
- 쿼리 상수는 대문자로 작성 (예: `SELECT_USER_BY_ID`)

### 6. 쿼리 Import 규칙
```python
# 올바른 방법
from backend.queries.user_queries import SELECT_USER_BY_ID
from backend.queries.item_queries import INSERT_ITEM

# 잘못된 방법
query = "SELECT * FROM users WHERE id = %(user_id)s"  # 직접 SQL 작성 금지
```

### 7. 응답 형식
- 모든 API 응답은 `ResponseModel` 사용
- 상태 코드는 문자열로 표현 (예: "200", "201", "204")
- 응답 메시지는 한글로 작성

### 8. 비동기 처리
- 모든 API 엔드포인트는 비동기 함수로 작성
- 데이터베이스 작업은 비동기로 처리

### 9. 타입 힌팅
- 모든 함수의 파라미터와 반환값에 타입 힌팅 추가
- 복잡한 타입은 `typing` 모듈 사용

### 10. 환경 변수
- 모든 설정은 환경 변수로 관리
- 환경 변수는 `.env` 파일에 정의
- 환경 변수는 `config.py`에서 로드

## 실행 방법
1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일 수정
```

4. 서버 실행
```bash
uvicorn main:app --reload
```

## API 문서
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 