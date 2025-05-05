# FastAPI 데모 프로젝트

이 프로젝트는 FastAPI 프레임워크를 사용한 기본적인 웹 API 예제입니다.

## 설치 방법

1. 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

## 실행 방법

서버 실행:
```bash
uvicorn app.main:app --port 9123 --reload
```

서버가 실행되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

- GET /: 기본 환영 메시지
- GET /items/{item_id}: 아이템 ID 조회 