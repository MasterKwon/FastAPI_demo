"""
기본 모델 클래스 정의
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class TimeStampModel(BaseModel):
    """타임스탬프 모델"""
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: Optional[datetime] = Field(None, description="수정 일시")

    model_config = ConfigDict(from_attributes=True) 