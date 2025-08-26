import asyncio
from typing import AsyncIterator, Awaitable, Callable

from typing_extensions import Annotated

from example.guber.server.application.gateway.payment import (
    PaymentGateway,
    get_payment_gateway,
)
from example.guber.server.application.internal_access import is_passenger
from example.guber.server.application.repo import PositionRepository, RideRepository
from example.guber.server.domain import Position, Ride, RideRequest, RideSnapshot
from example.guber.server.domain import accept_ride as accept_ride_rules
from example.guber.server.domain import finish_ride as finish_ride_rules
from example.guber.server.domain import start_ride as start_ride_rules
from example.guber.server.domain import update_position as update_position_rules
from example.guber.server.domain.entity.ride_rules import make_ride_id
from grpcAPI.app import APIPackage
from grpcAPI.data_types import Depends, FromRequest
from grpcAPI.protobuf import Empty, ProtoKey, ProtoStr, ProtoValue, StringValue

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
    id: Annotated[str, Depends(make_ride_id)],
    is_passenger: Annotated[Callable[[str], Awaitable[bool]], Depends(is_passenger)],
    ride_repo: RideRepository,
) -> StringValue:

    if not await is_passenger(passenger_id):
        raise ValueError("This account is not from a passenger")

    has_active_ride = await ride_repo.has_active_ride_by_passenger(passenger_id)
    if has_active_ride:
        raise ValueError("This passenger has an active ride")

    ride_id = await ride_repo.create_ride(id, request)
    return StringValue(value=ride_id)


driver_module = ride_package.make_module("driver")

driver_services = driver_module.make_service("driver_ride_actions")


@driver_services(tags=["write:ride", "read:account"])
async def accept_ride(
    ride_id: ProtoKey,
    driver_id: ProtoValue,
    is_passenger: Annotated[Callable[[str], Awaitable[bool]], Depends(is_passenger)],
    ride_repo: RideRepository,
) -> Empty:

    if await is_passenger(driver_id):
        raise ValueError("This account is not from a driver")

    has_active_ride = await ride_repo.has_active_ride_by_driver(driver_id)
    if has_active_ride:
        raise ValueError("This driver has an active ride")

    ride = await ride_repo.get_by_ride_id(ride_id)
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
    ride_repo: RideRepository,
    position_repo: PositionRepository,
) -> RideSnapshot:

    ride = await ride_repo.get_by_ride_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride with id {ride_id} not found")
    current_location = await position_repo.get_current_position(ride_id)
    return RideSnapshot(ride=ride, current_location=current_location)


@ride_services
async def start_ride(
    ride_id: ProtoStr,
    ride_repo: RideRepository,
    position_repo: PositionRepository,
) -> Empty:
    ride = await ride_repo.get_by_ride_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride with id {ride_id} not found")

    start_ride_rules(ride)
    await position_repo.create_position(
        ride_id, ride.start_point, ride.accepted_at.ToDatetime()
    )
    await ride_repo.update_ride(ride)

    return Empty()


@ride_services
async def update_position(
    position: Position,
    ride_repo: RideRepository,
    position_repo: PositionRepository,
) -> Empty:
    ride_id = position.ride_id
    ride = await ride_repo.get_by_ride_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride with id {ride_id} not found")

    last_position = await position_repo.get_current_position(ride_id)
    if last_position is None:
        raise ValueError(f"Last position not found for ride id {ride_id}")

    update_position_rules(ride, last_position.coord, position.coord)
    await ride_repo.update_ride(ride)

    await position_repo.update_position(position)

    return Empty()


@ride_services
async def finish_ride(
    ride_id: ProtoStr,
    ride_repo: RideRepository,
    payment_gateway: Annotated[PaymentGateway, Depends(get_payment_gateway)],
) -> Empty:

    ride = await ride_repo.get_by_ride_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride with id {ride_id} not found")
    finish_ride_rules(ride)
    await payment_gateway.process_payment({"rideId": ride.ride_id, "amount": ride.fare})
    await ride_repo.update_ride(ride)
    return Empty()


@ride_services
async def update_position_stream(
    position_stream: AsyncIterator[Position],
    ride_repo: RideRepository,
    position_repo: PositionRepository,
) -> Empty:

    ride = None

    async def _get_ride(id: str) -> Ride:
        ride = await ride_repo.get_by_ride_id(id)
        if ride is None:
            raise ValueError(f"Ride with id {id} not found")
        return ride

    ride_id = None
    async for position in position_stream:
        if ride_id is not None and ride_id != position.ride_id:
            raise ValueError(f"Unexpected ride_id: {position.ride_id}")
        ride_id = position.ride_id
        if ride is None:
            ride = await _get_ride(ride_id)

        last_position = await position_repo.get_current_position(ride_id)
        if last_position is None:
            raise ValueError(f"Last position not found for ride id {ride_id}")

        update_position_rules(ride, last_position.coord, position.coord)
        await ride_repo.update_ride(ride)
        await position_repo.update_position(position)
    return Empty()


def get_counter() -> int:
    return 10


def get_delay() -> float:
    return 30.0


@ride_services
async def get_position_stream(
    ride_id: StringValue,
    ride_repo: RideRepository,
    position_repo: PositionRepository,
    counter: Annotated[int, Depends(get_counter)],
    delay: Annotated[float, Depends(get_delay)],
) -> AsyncIterator[Position]:

    if counter < 1:
        counter = 1
    for _ in range(counter):
        current_position = await position_repo.get_current_position(ride_id.value)
        if current_position is None:
            raise ValueError(f"Current position not found for ride id {ride_id.value}")
        yield current_position
        await asyncio.sleep(delay)

        if await ride_repo.is_ride_finished(ride_id.value):
            break
