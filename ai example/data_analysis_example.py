from backend.utils.ai.data_analysis import (
    analyze_data_patterns,
    analyze_time_series,
    check_data_quality,
    extract_data_insights
)

# 샘플 데이터
sales_data = [
    {"date": "2024-01-01", "sales": 1000, "product": "A", "region": "서울"},
    {"date": "2024-01-02", "sales": 1200, "product": "A", "region": "서울"},
    {"date": "2024-01-03", "sales": 900, "product": "A", "region": "서울"},
    {"date": "2024-01-04", "sales": 1100, "product": "A", "region": "서울"},
    {"date": "2024-01-05", "sales": 1300, "product": "A", "region": "서울"},
]

# 데이터 스키마
schema = {
    "date": "날짜 (YYYY-MM-DD)",
    "sales": "판매액 (원)",
    "product": "제품 코드",
    "region": "지역"
}

# 1. 데이터 패턴 분석
print("=== 데이터 패턴 분석 ===")
pattern = analyze_data_patterns(sales_data, "일별 판매 데이터")
print(f"패턴 유형: {pattern.pattern_type}")
print(f"설명: {pattern.description}")
print(f"신뢰도: {pattern.confidence}")
print("시사점:")
for implication in pattern.implications:
    print(f"- {implication}")
print()

# 2. 시계열 분석
print("=== 시계열 분석 ===")
time_series = analyze_time_series(sales_data, "date", "sales")
print(f"추세: {time_series.trend}")
print(f"계절성: {time_series.seasonality}")
print("이상치:")
for anomaly in time_series.anomalies:
    print(f"- {anomaly}")
print(f"예측: {time_series.forecast}")
print()

# 3. 데이터 품질 검사
print("=== 데이터 품질 검사 ===")
quality = check_data_quality(sales_data, schema)
print("이슈:")
for issue in quality.issues:
    print(f"- {issue}")
print("권장사항:")
for recommendation in quality.recommendations:
    print(f"- {recommendation}")
print(f"전체 품질: {quality.overall_quality}")
print()

# 4. 비즈니스 인사이트 추출
print("=== 비즈니스 인사이트 ===")
insights = extract_data_insights(
    sales_data,
    "서울 지역의 제품 A 판매 데이터"
)
print("주요 발견사항:")
for finding in insights.key_findings:
    print(f"- {finding}")
print("권장사항:")
for recommendation in insights.recommendations:
    print(f"- {recommendation}")
print(f"비즈니스 영향: {insights.business_impact}") 