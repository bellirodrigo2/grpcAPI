from typing import Any, Optional

from sqlalchemy import select

from example.guber.server.adapters.repo.sqlalchemy import RideDB
from example.guber.server.adapters.repo.sqlalchemy import RideStatus as RideStatusDB
from example.guber.server.adapters.repo.sqlalchemy import SqlAlchemyDB
from example.guber.server.application.repo import RideRepo
from example.guber.server.domain import Ride, RideRequest, RideStatus
from grpcAPI.protobuf import Timestamp


class SqlAlchemyRideRepo(RideRepo, SqlAlchemyDB):

    async def has_active_ride(self, passenger_id: str) -> bool:

        result = await self.db.execute(
            select(RideDB).where(
                RideDB.passenger_id == passenger_id,
                RideDB.status == RideStatusDB.IN_PROGRESS,
            )
        )
        return result.scalars().first() is not None

    async def get_by_ride_id(self, ride_id: str) -> Optional[Ride]:
        result = await self.db.execute(select(RideDB).where(RideDB.ride_id == ride_id))
        ride = result.scalar_one_or_none()

        return orm_to_proto(ride)

    async def create_ride(self, request: RideRequest) -> str: ...

    async def update_ride(self, ride: Ride) -> None: ...

    async def is_ride_finished(self, ride_id: str) -> bool: ...


async def get_ride_repo(**kwargs: Any) -> RideRepo:  # type: ignore
    pass


def orm_to_proto(ride: Optional[RideDB]) -> Optional[Ride]:
    if ride is None:
        return None
    ride_request = RideRequest(
        passenger_id=ride.passenger_id,
        from_lat=ride.from_lat,
        from_long=ride.from_long,
        to_lat=ride.to_lat,
        to_long=ride.to_long,
    )
    accepted_at = (
        Timestamp().FromDatetime(ride.accepted_at) if ride.accepted_at else None
    )
    finished_at = (
        Timestamp().FromDatetime(ride.finished_at) if ride.finished_at else None
    )
    status_val = RideStatus.Value(ride.status.name)
    return Ride(
        ride_id=ride.id,
        driver_id=ride.driver_id if ride.driver_id else "",
        ride_request=ride_request,
        fare=ride.fare,
        status=RideStatus.Name(status_val),
        accepted_at=accepted_at,
        finished_at=finished_at,
    )
