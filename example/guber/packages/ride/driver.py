from typing_extensions import Annotated
from grpcAPI.data_types import Depends
from grpcAPI.prototypes import KeyValueStr, Empty


from example.guber.auth import async_authentication
from example.guber.packages.account import AccountRepo, get_account_repo
from example.guber.packages.ride import ride_package, RideRepo, get_ride_repo
from example.guber.domain import accept_ride as accept_ride_domain

driver_module = ride_package.make_module("driver")

driver_services = driver_module.make_service("driver_ride_actions")


@driver_services(request_type_input=KeyValueStr)
async def accept_ride(
    key: Annotated[str, "ride_id"],
    value: Annotated[str, "driver_id"],
    _: Annotated[None, Depends(async_authentication, order=0)],
    acc_repo: Annotated[AccountRepo, Depends(get_account_repo)],
    ride_repo: Annotated[RideRepo, Depends(get_ride_repo)],
) -> Empty:

    has_active_ride = await ride_repo.has_active_ride(value)
    if has_active_ride:
        raise ValueError("This driver has an active ride")

    account = await acc_repo.get_by_id(value)
    if account is None:
        raise ValueError(f"Account not found: Id: {value}")
    ride = await ride_repo.get_by_id(key)
    accept_ride_domain(ride, account)
    await ride_repo.update_ride(ride)

    return Empty()
