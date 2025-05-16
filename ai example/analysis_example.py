from backend.config import settings
from backend.utils.ai.ai_analysis import analyze_sentiment, classify_text, extract_keywords

# API 키 설정
api_key = settings.OPENAI_API_KEY
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# 테스트할 텍스트
text = """
이 제품은 정말 놀라운 성능을 보여줍니다. 사용하기 쉽고 디자인도 세련되었습니다.
다만 가격이 조금 비싸다는 점이 아쉽습니다. 전반적으로 만족스러운 구매였습니다.
"""

# 1. 감정 분석
print("=== 감정 분석 ===")
sentiment = analyze_sentiment(text, score=4)
print(f"감정: {sentiment.sentiment}")
print(f"신뢰도: {sentiment.confidence}")
print(f"설명: {sentiment.explanation}")
print()

# 2. 텍스트 분류
print("=== 텍스트 분류 ===")
categories = ["제품 리뷰", "고객 문의", "불만 사항", "칭찬"]
classification = classify_text(text, categories)
print(f"카테고리: {classification.category}")
print(f"신뢰도: {classification.confidence}")
print(f"설명: {classification.explanation}")
print()

# 3. 키워드 추출
print("=== 키워드 추출 ===")
keywords = extract_keywords(text)
print("주요 키워드:", ", ".join(keywords)) 