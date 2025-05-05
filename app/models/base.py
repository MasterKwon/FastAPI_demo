"""
기본 모델 정의
"""
from pydantic import BaseModel
from datetime import datetime

class TimeStampModel(BaseModel):
    """타임스탬프 기본 모델"""
    created_at: datetime

    class Config:
        from_attributes = True 