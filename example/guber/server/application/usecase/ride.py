from typing_extensions import Annotated

from example.guber.server.application.gateway import Authenticate
from example.guber.server.application.gateway.payment import (
    PaymentGateway,
    get_payment_gateway,
)
from example.guber.server.application.internal_access import (
    is_passenger,
    passenger_name,
)
from example.guber.server.application.repo import PositionRepository, RideRepository
from example.guber.server.domain import Position, RideInfo, RideRequest
from example.guber.server.domain.entity.ride_rules import (
    accept_ride as accept_ride_rules,
)
from example.guber.server.domain.entity.ride_rules import (
    finish_ride as finish_ride_rules,
)
from example.guber.server.domain.entity.ride_rules import start_ride as start_ride_rules
from example.guber.server.domain.entity.ride_rules import (
    update_position as update_position_rules,
)
from grpcAPI.app import APIPackage
from grpcAPI.data_types import Depends, FromRequest
from grpcAPI.protobuf import Empty, ProtoKey, ProtoValue, StringValue
from grpcAPI.protobuf.deriveds import ProtoStr

ride_package = APIPackage("ride")


def passenger_id_validator(value: str) -> str:
    if not value:
        raise ValueError("Passenger Id is required")
    return value


PassengerId = Annotated[str, FromRequest(RideRequest, validator=passenger_id_validator)]


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


driver_module = ride_package.make_module("driver")

driver_services = driver_module.make_service("driver_ride_actions")


@driver_services(tags=["write:ride", "read:account"])
async def accept_ride(
    ride_id: ProtoKey,
    driver_id: ProtoValue,
    _: Authenticate,
    is_passenger: Annotated[bool, Depends(is_passenger)],
    ride_repo: RideRepository,
) -> Empty:

    if is_passenger:
        raise ValueError("This account is not from a driver")

    has_active_ride = await ride_repo.has_active_ride(driver_id)
    if has_active_ride:
        raise ValueError("This driver has an active ride")

    ride = await ride_repo.get_by_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride not found: Id: {ride_id}")
    accept_ride_rules(ride, driver_id)
    await ride_repo.update_ride(ride)

    return Empty()


ride_module = ride_package.make_module("ride")

ride_services = ride_module.make_service("ride_actions")


@ride_services
async def get_ride(
    ride_id: ProtoStr,
    _: Authenticate,
    passenger_name: Annotated[str, Depends(passenger_name)],
    ride_repo: RideRepository,
    position_repo: PositionRepository,
) -> RideInfo:

    ride = await ride_repo.get_by_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride with id {ride_id} not found")
    lat, long = await position_repo.get_current_position(ride_id)
    return RideInfo(
        ride=ride, passenger_name=passenger_name, current_lat=lat, current_long=long
    )


@ride_services
async def start_ride(
    ride_id: ProtoStr,
    _: Authenticate,
    ride_repo: RideRepository,
) -> Empty:
    ride = await ride_repo.get_by_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride with id {ride_id} not found")

    start_ride_rules(ride)
    await ride_repo.update_ride(ride)

    return Empty()


@ride_services
async def update_position(
    position: Position,
    _: Authenticate,
    ride_repo: RideRepository,
    position_repo: PositionRepository,
) -> Empty:
    ride_id = position.ride_id
    ride = await ride_repo.get_by_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride with id {ride_id} not found")

    last_lat, last_long = await position_repo.get_current_position(ride_id)

    update_position_rules(ride, (last_lat, last_long), (position.lat, position.long))
    await ride_repo.update_ride(ride)

    return Empty()


@ride_services
async def finish_ride(
    ride_id: ProtoStr,
    _: Authenticate,
    ride_repo: RideRepository,
    payment_gateway: Annotated[PaymentGateway, Depends(get_payment_gateway)],
) -> Empty:

    ride = await ride_repo.get_by_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride with id {ride_id} not found")
    finish_ride_rules(ride)
    await payment_gateway.process_payment({"rideId": ride.ride_id, "amount": ride.fare})
    await ride_repo.update_ride(ride)
    return Empty()
