from typing_extensions import Annotated
from grpcAPI.data_types import Depends

from example.guber.packages.account import AccountRepo, get_account_repo

from example.guber.auth import async_authentication
from example.guber.packages.ride import (
    ride_package,
    RideRequest,
    get_ride_repo,
    RideRepo,
)

user_module = ride_package.make_module("user")

user_services = user_module.make_service("user_ride_actions")


@user_services
async def request_ride(
    request: RideRequest,
    _: Annotated[None, Depends(async_authentication, order=0)],
    acc_repo: Annotated[AccountRepo, Depends(get_account_repo)],
    ride_repo: Annotated[RideRepo, Depends(get_ride_repo)],
) -> str:

    # VER SE DA PRA USAR o MESMO DB CONNECTION PARA OS DOIS REPO
    # OU SE GET_ACCOUNT_REPO FOR UMA FUNÇÃO COM ORDER 1 com raise e GET_RIDE_REPO ORDER 2

    account = await acc_repo.get_by_id(request.passenger_id)
    if account is None:
        raise ValueError("Account not found")
    if account.info.is_driver:
        raise ValueError("This account is not from passenger")

    has_active_ride = await ride_repo.has_active_ride(request.passenger_id)
    if has_active_ride:
        raise ValueError("This passenger has an active ride")

    return await ride_repo.create_ride(request)
