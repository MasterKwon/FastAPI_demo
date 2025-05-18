from typing import Dict, List, Optional
import openai
from pydantic import BaseModel
from backend.core.config import settings

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

class SentimentAnalysis(BaseModel):
    sentiment: str  # GOOD, BAD, NATURAL
    confidence: float
    explanation: str

class TextClassification(BaseModel):
    category: str
    confidence: float
    explanation: str

def analyze_sentiment(text: str, score: int, model: str = "gpt-3.5-turbo") -> SentimentAnalysis:
    """
    회원이 작성한 리뷰와 점수를 분석합니다.
    :param text: 분석할 리뷰내용
    :param score: 리뷰점수(1~5)
    :param model: 사용할 OpenAI 모델 (기본값: gpt-3.5-turbo)
    :return: 감정 분석 결과
    """
    prompt = f"""
    다음 리뷰의 감정을 사용자의 점수에 따라 분석하고 다음 정보를 제공해주세요:
    1. 감정 (GOOD:긍정적/BAD:부정적/NATURAL:중립적)
    2. 신뢰도(%) (0-100)
    3. 간단한 설명

    리뷰: {text}
    
    점수: {score}
    
    JSON 형식으로 응답해주세요:
    {{
        "sentiment": "GOOD/BAD/NATURAL",
        "confidence": 95,
        "explanation": "감정 분석 결과"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 감정 분석 전문가입니다. 모든 응답은 한글로 해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        result = eval(response.choices[0].message.content)
        return SentimentAnalysis(**result)
    except Exception as e:
        return SentimentAnalysis(
            sentiment="ERROR",
            confidence=0.0,
            explanation=f"분석 중 오류 발생: {str(e)}"
        )

def classify_text(text: str, categories: List[str], model: str = "gpt-3.5-turbo") -> TextClassification:
    """
    텍스트를 주어진 카테고리 중 하나로 분류합니다.
    :param text: 분류할 텍스트
    :param categories: 가능한 카테고리 목록
    :param model: 사용할 OpenAI 모델 (기본값: gpt-3.5-turbo)
    :return: 분류 결과
    """
    prompt = f"""
    다음 텍스트를 다음 카테고리 중 하나로 분류해주세요: {', '.join(categories)}
    
    텍스트: {text}
    
    JSON 형식으로 응답해주세요:
    {{
        "category": "선택된_카테고리",
        "confidence": 0.95,
        "explanation": "간단한 설명"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 텍스트 분류 전문가입니다. 모든 응답은 한글로 해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        result = eval(response.choices[0].message.content)
        return TextClassification(**result)
    except Exception as e:
        return TextClassification(
            category="오류",
            confidence=0.0,
            explanation=f"분류 중 오류 발생: {str(e)}"
        )

def extract_keywords(text: str, max_keywords: int = 5, model: str = "gpt-3.5-turbo") -> List[str]:
    """
    텍스트에서 주요 키워드를 추출합니다.
    :param text: 분석할 텍스트
    :param max_keywords: 추출할 최대 키워드 수
    :param model: 사용할 OpenAI 모델 (기본값: gpt-3.5-turbo)
    :return: 키워드 목록
    """
    prompt = f"""
    다음 텍스트에서 가장 중요한 {max_keywords}개의 키워드를 추출해주세요.
    키워드만 쉼표로 구분하여 나열해주세요.

    텍스트: {text}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "당신은 키워드 추출 전문가입니다. 모든 응답은 한글로 해주세요."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        keywords = response.choices[0].message.content.strip().split(',')
        return [k.strip() for k in keywords]
    except Exception as e:
        return [f"키워드 추출 중 오류 발생: {str(e)}"] 