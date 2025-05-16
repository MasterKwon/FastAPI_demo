"""
비밀번호 해싱 관련 유틸리티 모듈
"""
import hashlib
import base64
import os

def get_password_hash(password: str) -> str:
    """
    비밀번호를 해시화하는 함수
    
    Args:
        password: 해시화할 비밀번호
    
    Returns:
        str: 해시화된 비밀번호
    """
    # 솔트 생성
    salt = os.urandom(16)
    
    # 비밀번호와 솔트를 결합하여 해시 생성
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # 반복 횟수
    )
    
    # 솔트와 해시를 결합하여 저장
    return base64.b64encode(salt + hashed).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호를 검증하는 함수
    
    Args:
        plain_password: 검증할 비밀번호
        hashed_password: 저장된 해시화된 비밀번호
    
    Returns:
        bool: 비밀번호가 일치하면 True, 아니면 False
    """
    try:
        # 저장된 해시에서 솔트와 해시 분리
        decoded = base64.b64decode(hashed_password)
        salt = decoded[:16]
        stored_hash = decoded[16:]
        
        # 입력된 비밀번호로 해시 생성
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            100000
        )
        
        # 해시 비교
        return stored_hash == new_hash
    except Exception:
        return False 