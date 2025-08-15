from grpcAPI.prototypes import KeyValueStr, Empty

from example.guber.application.services.auth import Authenticate
from example.guber.application.repo import AccountRepository
from example.guber.application.usecase.ride import ride_package, RideRepository
from example.guber.domain import accept_ride as accept_ride_domain
from grpcAPI.prototypes.deriveds import ProtoKey, ProtoValue

driver_module = ride_package.make_module("driver")

driver_services = driver_module.make_service("driver_ride_actions")


@driver_services(request_type_input=KeyValueStr)
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
