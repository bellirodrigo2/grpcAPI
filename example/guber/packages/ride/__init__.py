from grpcAPI.app import APIPackage


from example.guber.repo.ride_repo import RideRepo, get_ride_repo
from example.guber.domain import Ride, RideRequest, RideStatus

ride_package = APIPackage("ride")

__all__ = [
    "ride_package",
    "Ride",
    "RideRequest",
    "RideStatus",
    "RideRepo",
    "get_ride_repo",
]
