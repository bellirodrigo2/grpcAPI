from pydantic import BaseModel


class CPF(BaseModel):
    value: str


class CarPlate(BaseModel):
    value: str
