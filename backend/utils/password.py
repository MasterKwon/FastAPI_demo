"""
비밀번호 해싱 관련 유틸리티 모듈
"""
from passlib.context import CryptContext
from backend.database.exceptions import ValidationError

# 비밀번호 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    비밀번호를 해시화하는 함수
    
    Args:
        password: 해시화할 비밀번호
    
    Returns:
        str: 해시화된 비밀번호
        
    Raises:
        ValidationError: 비밀번호가 유효하지 않은 경우
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise ValidationError(f"비밀번호 해시화 실패: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호를 검증하는 함수
    
    Args:
        plain_password: 검증할 비밀번호
        hashed_password: 저장된 해시화된 비밀번호
    
    Returns:
        bool: 비밀번호가 일치하면 True, 아니면 False
        
    Raises:
        ValidationError: 비밀번호 검증 중 오류 발생 시
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        raise ValidationError(f"비밀번호 검증 실패: {str(e)}") 