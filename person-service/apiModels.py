# Pydantic-модели для FastAPI

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# тело запроса на создание/обновление
class PersonRequest(BaseModel):
    name: str = Field(..., min_length=1)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    address: Optional[str] = None
    work: Optional[str] = None


# ответ с id
class PersonResponse(BaseModel):
    id: int
    name: str
    age: Optional[int] = None
    address: Optional[str] = None
    work: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel): # для ошибки 404
    message: str


class ValidationErrorResponse(BaseModel): # для ошибки 400
    message: str
    errors: dict[str, str]