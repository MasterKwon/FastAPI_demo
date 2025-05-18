from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI
from backend.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class DataPattern(BaseModel):
    pattern_type: str
    description: str
    confidence: float
    implications: List[str]

class TimeSeriesAnalysis(BaseModel):
    trend: str
    seasonality: Optional[str]
    anomalies: List[Dict[str, Any]]
    forecast: Optional[str]

class DataQuality(BaseModel):
    issues: List[str]
    recommendations: List[str]
    overall_quality: str

class DataInsight(BaseModel):
    key_findings: List[str]
    recommendations: List[str]
    business_impact: str

def analyze_data_patterns(data: List[Dict[str, Any]], context: str = "", model: str = "gpt-3.5-turbo") -> DataPattern:
    """
    데이터에서 패턴을 분석합니다.
    
    Args:
        data: 분석할 데이터 리스트
        context: 데이터에 대한 추가 컨텍스트 정보
        model: 사용할 OpenAI 모델 (기본값: gpt-3.5-turbo)
    
    Returns:
        DataPattern: 분석된 패턴 정보
    """
    prompt = f"""
    다음 데이터에서 패턴을 분석해주세요:
    
    컨텍스트: {context}
    데이터: {data}
    
    다음 형식으로 응답해주세요:
    - 패턴 유형
    - 패턴 설명
    - 신뢰도 (0-1)
    - 시사점
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "당신은 데이터 분석 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    # 응답 파싱 및 DataPattern 객체 생성
    # 실제 구현에서는 응답을 적절히 파싱하여 DataPattern 객체를 생성해야 합니다
    return DataPattern(
        pattern_type="예시 패턴",
        description="예시 설명",
        confidence=0.95,
        implications=["예시 시사점"]
    )

def analyze_time_series(data: List[Dict[str, Any]], time_column: str, value_column: str, model: str = "gpt-3.5-turbo") -> TimeSeriesAnalysis:
    """
    시계열 데이터를 분석합니다.
    
    Args:
        data: 시계열 데이터 리스트
        time_column: 시간 컬럼명
        value_column: 값 컬럼명
        model: 사용할 OpenAI 모델 (기본값: gpt-3.5-turbo)
    
    Returns:
        TimeSeriesAnalysis: 시계열 분석 결과
    """
    prompt = f"""
    다음 시계열 데이터를 분석해주세요:
    
    데이터: {data}
    시간 컬럼: {time_column}
    값 컬럼: {value_column}
    
    다음 항목들을 분석해주세요:
    - 추세
    - 계절성
    - 이상치
    - 향후 예측
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "당신은 시계열 데이터 분석 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    # 응답 파싱 및 TimeSeriesAnalysis 객체 생성
    return TimeSeriesAnalysis(
        trend="예시 추세",
        seasonality="예시 계절성",
        anomalies=[],
        forecast="예시 예측"
    )

def check_data_quality(data: List[Dict[str, Any]], schema: Dict[str, str], model: str = "gpt-3.5-turbo") -> DataQuality:
    """
    데이터 품질을 검사합니다.
    
    Args:
        data: 검사할 데이터 리스트
        schema: 데이터 스키마 정의
        model: 사용할 OpenAI 모델 (기본값: gpt-3.5-turbo)
    
    Returns:
        DataQuality: 데이터 품질 검사 결과
    """
    prompt = f"""
    다음 데이터의 품질을 검사해주세요:
    
    데이터: {data}
    스키마: {schema}
    
    다음 항목들을 검사해주세요:
    - 데이터 품질 이슈
    - 개선 권장사항
    - 전반적인 품질 평가
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "당신은 데이터 품질 관리 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    # 응답 파싱 및 DataQuality 객체 생성
    return DataQuality(
        issues=["예시 이슈"],
        recommendations=["예시 권장사항"],
        overall_quality="예시 품질 평가"
    )

def extract_data_insights(data: List[Dict[str, Any]], business_context: str = "", model: str = "gpt-3.5-turbo") -> DataInsight:
    """
    데이터에서 비즈니스 인사이트를 추출합니다.
    
    Args:
        data: 분석할 데이터 리스트
        business_context: 비즈니스 컨텍스트 정보
        model: 사용할 OpenAI 모델 (기본값: gpt-3.5-turbo)
    
    Returns:
        DataInsight: 추출된 인사이트
    """
    prompt = f"""
    다음 데이터에서 비즈니스 인사이트를 추출해주세요:
    
    데이터: {data}
    비즈니스 컨텍스트: {business_context}
    
    다음 항목들을 분석해주세요:
    - 주요 발견사항
    - 권장사항
    - 비즈니스 영향
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "당신은 비즈니스 인텔리전스 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    # 응답 파싱 및 DataInsight 객체 생성
    return DataInsight(
        key_findings=["예시 발견사항"],
        recommendations=["예시 권장사항"],
        business_impact="예시 비즈니스 영향"
    ) 