
from example.guber.server.application.gateway import (
    Authenticate,
)
from example.guber.server.application.repo import PositionRepository, RideRepository
from example.guber.server.application.usecase.ride import (
    Position,
    ride_package,
)
from example.guber.server.domain import update_position as update_position_rules
from grpcAPI.protobuf import Empty

ride_module = ride_package.make_module("ride")

ride_services = ride_module.make_service("ride_actions")


# Temporarily commented out due to ProtoStr dependency resolution issues
# @ride_services
# async def get_ride(
#     ride_id: ProtoStr,
#     _: Authenticate,
#     passenger_name: Annotated[str, Depends(passenger_name)],
#     ride_repo: RideRepository,
#     position_repo: PositionRepository,
# ) -> RideInfo:

#     ride = await ride_repo.get_by_id(ride_id)
#     if ride is None:
#         raise ValueError(f"Ride with id {ride_id} not found")
#     lat, long = await position_repo.get_current_position(ride_id)
#     return RideInfo(
#         ride=ride, passenger_name=passenger_name, current_lat=lat, current_long=long
#     )


# Temporarily commented out due to ProtoStr dependency resolution issues
# @ride_services
# async def start_ride(
#     ride_id: ProtoStr,
#     _: Authenticate,
#     ride_repo: RideRepository,
# ) -> Empty:
#     ride = await ride_repo.get_by_id(ride_id)
#     if ride is None:
#         raise ValueError(f"Ride with id {ride_id} not found")

#     start_ride_rules(ride)
#     await ride_repo.update_ride(ride)

#     return Empty()


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


# Temporarily commented out due to ProtoStr dependency resolution issues
# @ride_services
# async def finish_ride(
#     ride_id: ProtoStr,
#     _: Authenticate,
#     ride_repo: RideRepository,
#     payment_gateway: Annotated[PaymentGateway, Depends(get_payment_gateway)],
# ) -> Empty:

#     ride = await ride_repo.get_by_id(ride_id)
#     if ride is None:
#         raise ValueError(f"Ride with id {ride_id} not found")
#     finish_ride_rules(ride)
#     await payment_gateway.process_payment({"rideId": ride.ride_id, "amount": ride.fare})
#     await ride_repo.update_ride(ride)
#     return Empty()
