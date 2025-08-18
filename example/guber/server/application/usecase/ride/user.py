from typing_extensions import Annotated

from example.guber.server.application.gateway import Authenticate
from example.guber.server.application.internal_access import is_passenger
from example.guber.server.application.repo import RideRepository
from example.guber.server.application.usecase.ride import (
    PassengerId,
    RideRequest,
    ride_package,
)
from grpcAPI.data_types import Depends
from grpcAPI.protobuf import StringValue

user_module = ride_package.make_module("user")

user_services = user_module.make_service("user_ride_actions")


@user_services(tags=["write:ride", "read:account"])
async def request_ride(
    request: RideRequest,
    passenger_id: PassengerId,
    _: Authenticate,
    is_passenger: Annotated[bool, Depends(is_passenger)],
    ride_repo: RideRepository,
) -> StringValue:

    if not is_passenger:
        raise ValueError("This account is not from a passenger")

    has_active_ride = await ride_repo.has_active_ride(passenger_id)
    if has_active_ride:
        raise ValueError("This passenger has an active ride")

    ride_id = await ride_repo.create_ride(request)
    return StringValue(value=ride_id)
