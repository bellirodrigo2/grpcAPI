from typing_extensions import Annotated

from example.guber.server.application.repo import RideRepo, get_ride_repo
from example.guber.server.domain import (
    Position,
    Ride,
    RideInfo,
    RideRequest,
    RideStatus,
)
from grpcAPI.app import APIPackage
from grpcAPI.data_types import FromRequest

ride_package = APIPackage("ride")


def passenger_id_validator(value: str) -> str:
    if not value:
        raise ValueError("Passenger Id is required")
    return value


PassengerId = Annotated[str, FromRequest(RideRequest, validator=passenger_id_validator)]

__all__ = [
    "ride_package",
    "Ride",
    "RideRequest",
    "RideStatus",
    "Position",
    "RideRepo",
    "get_ride_repo",
    "PassengerId",
    "RideInfo",
]
