import openai
from backend.config import settings

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def openai_translate(text: str, target_lang: str, model: str = "gpt-3.5-turbo") -> str:
    """
    텍스트를 지정된 언어로 번역합니다.
    
    Args:
        text: 번역할 텍스트
        target_lang: 대상 언어
        model: 사용할 OpenAI 모델 (기본값: gpt-3.5-turbo)
    
    Returns:
        str: 번역된 텍스트
    """
    prompt = f"Translate the following text to {target_lang}:\n{text}"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful translator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"번역 중 오류 발생: {str(e)}"