import re
from typing import Any

from pydantic import EmailStr


def luhn_check(number: str) -> bool:
    digits = [int(d) for d in number]
    checksum = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:  # posições pares (baseado em 0)
            dbl = d * 2
            checksum += dbl if dbl < 10 else dbl - 9
        else:
            checksum += d
    return checksum % 10 == 0


def validate_sin(v: str, **kwargs: Any) -> str:
    v = v.replace(" ", "").strip()
    if not re.fullmatch(r"\d{9}", v):
        raise ValueError("SIN should have exactly 9 digits")
    if not luhn_check(v):
        raise ValueError("Invalid SIN (failed Luhn check)")
    return v


def validate_car_plate(v: str, **kwargs: Any) -> str:
    if v == "":
        return v
    v = v.replace(" ", "").strip()
    if not re.fullmatch(r"[A-Z]{3}-\d{4}", v):
        raise ValueError("Invalid car plate format")
    return v


__all__ = ["validate_sin", "validate_car_plate", "EmailStr"]
