from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    data: Optional[T] = None
    message: str = "Success"
    status_code: str = "200" 