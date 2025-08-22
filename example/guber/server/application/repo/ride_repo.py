from typing_extensions import Any, Optional, Protocol

from example.guber.server.domain import Ride, RideRequest


class RideRepo(Protocol):

    async def has_active_ride_by_passenger(self, passenger_id: str) -> bool: ...
    async def has_active_ride_by_driver(self, driver_id: str) -> bool: ...

    async def get_by_ride_id(self, ride_id: str) -> Optional[Ride]: ...

    async def create_ride(self, id: str, request: RideRequest) -> str: ...

    async def update_ride(self, ride: Ride) -> None: ...

    async def is_ride_finished(self, ride_id: str) -> bool: ...


async def get_ride_repo(**kwargs: Any) -> RideRepo:  # type: ignore
    pass
