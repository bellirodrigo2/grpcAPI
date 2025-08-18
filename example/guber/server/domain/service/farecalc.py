from datetime import datetime
from typing import Protocol


class FareCalculator(Protocol):
    def calculate(self, distance: int) -> float: ...


class SundayFare:

    rate = 5.0

    def calculate(self, distance: int) -> float:
        return distance * self.rate


class OvernightFare:

    rate = 3.9

    def calculate(self, distance: int) -> float:
        return distance * self.rate


class NormalFare:

    rate = 2.1

    def calculate(self, distance: int) -> float:
        return distance * self.rate


def create_fare_calculator(date: datetime) -> FareCalculator:
    if date.weekday() == 6:  # Sunday
        return SundayFare()
    elif date.hour < 8 or date.hour > 18:  # Overnight
        return OvernightFare()
    else:  # Normal hours
        return NormalFare()
