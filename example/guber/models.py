__all__ = ["CPF", "CarPlate", "EmailStr"]
from pydantic import BaseModel, EmailStr


class CPF(BaseModel):
    value: str


class CarPlate(BaseModel):
    value: str
