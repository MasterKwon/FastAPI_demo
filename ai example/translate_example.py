from backend.config import settings
from backend.utils.ai.translate import openai_translate

text = "안녕하세요, 반갑습니다."
print(openai_translate(text, "English"))
