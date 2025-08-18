from typing_extensions import Annotated

from example.guber.server.application.repo.account_repo import (
    AccountRepo,
    get_account_repo,
)
from example.guber.server.application.repo.position_repo import (
    PositionRepo,
    get_position_repo,
)
from example.guber.server.application.repo.ride_repo import RideRepo, get_ride_repo
from grpcAPI.data_types import Depends

AccountRepository = Annotated[AccountRepo, Depends(get_account_repo)]
RideRepository = Annotated[RideRepo, Depends(get_ride_repo)]
PositionRepository = Annotated[PositionRepo, Depends(get_position_repo)]


__all__ = [
    "AccountRepo",
    "get_account_repo",
    "RideRepo",
    "get_ride_repo",
    "AccountRepository",
    "RideRepository",
]
