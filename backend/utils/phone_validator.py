import phonenumbers
from typing import Optional, Tuple

def validate_phone_number(phone_number: str, country_code: str = "KR") -> Tuple[bool, Optional[str]]:
    """
    전화번호의 유효성을 검증합니다.
    
    Args:
        phone_number (str): 검증할 전화번호
        country_code (str): 국가 코드 (기본값: "KR")
        
    Returns:
        Tuple[bool, Optional[str]]: (유효성 여부, 오류 메시지)
    """
    try:
        # 전화번호 파싱
        parsed_number = phonenumbers.parse(phone_number, country_code)
        
        # 유효성 검증
        if not phonenumbers.is_valid_number(parsed_number):
            return False, "유효하지 않은 전화번호 형식입니다."
            
        # 국제 형식으로 변환
        formatted_number = phonenumbers.format_number(
            parsed_number, 
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        
        return True, formatted_number
        
    except phonenumbers.phonenumberutil.NumberParseException as e:
        return False, f"전화번호 파싱 오류: {str(e)}"
    except Exception as e:
        return False, f"전화번호 검증 중 오류 발생: {str(e)}" 