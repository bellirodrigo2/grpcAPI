from example.guber.application.repo import AccountRepository, RideRepository

from example.guber.application.services import Authenticate
from example.guber.application.usecase.ride import (
    ride_package,
    RideRequest,
    PassengerId
)

user_module = ride_package.make_module("user")

user_services = user_module.make_service("user_ride_actions")

@user_services
async def request_ride(
    request: RideRequest,
    passenger_id: PassengerId,
    _: Authenticate,
    acc_repo: AccountRepository,
    ride_repo: RideRepository,
) -> str:

    # VER SE DA PRA USAR o MESMO DB CONNECTION PARA OS DOIS REPO
    # OU SE GET_ACCOUNT_REPO FOR UMA FUNÇÃO COM ORDER 1 com raise e GET_RIDE_REPO ORDER 2

    account = await acc_repo.get_by_id(passenger_id)
    if account is None:
        raise ValueError("Account not found")
    if account.info.is_driver:
        raise ValueError("This account is not from passenger")

    has_active_ride = await ride_repo.has_active_ride(passenger_id)
    if has_active_ride:
        raise ValueError("This passenger has an active ride")

    return await ride_repo.create_ride(request)
