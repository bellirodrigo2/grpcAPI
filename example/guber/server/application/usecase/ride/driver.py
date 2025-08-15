from grpcAPI.prototypes import KeyValueStr, Empty,ProtoKey, ProtoValue

from example.guber.server.application.services import Authenticate
from example.guber.server.application.repo import AccountRepository, RideRepository
from example.guber.server.application.usecase.ride import ride_package
from example.guber.server.domain import accept_ride as accept_ride_domain

driver_module = ride_package.make_module("driver")

driver_services = driver_module.make_service("driver_ride_actions")


@driver_services(request_type_input=KeyValueStr, tags=["write:ride", 'read:account'])
async def accept_ride(
    ride_id: ProtoKey,
    driver_id: ProtoValue,
    _: Authenticate,
    acc_repo: AccountRepository,
    ride_repo: RideRepository,
) -> Empty:

    has_active_ride = await ride_repo.has_active_ride(driver_id)
    if has_active_ride:
        raise ValueError("This driver has an active ride")

    account = await acc_repo.get_by_id(driver_id)
    if account is None:
        raise ValueError(f"Account not found: Id: {driver_id}")
    ride = await ride_repo.get_by_id(ride_id)
    if ride is None:
        raise ValueError(f"Ride not found: Id: {ride_id}")
    accept_ride_domain(ride, account)
    await ride_repo.update_ride(ride)

    return Empty()
