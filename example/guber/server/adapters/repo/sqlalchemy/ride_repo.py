from typing import Optional

from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy import select

from example.guber.adapters.repo.sqlalchemy import RideDB, SqlAlchemyDB
from example.guber.application.repo import RideRepo
from example.guber.domain import Ride, RideRequest


class SqlAlchemyRideRepo(RideRepo, SqlAlchemyDB):
    async def has_active_ride(self, passenger_id: str) -> bool:
        results = await self.db.execute(
            select(RideDB).where(
                RideDB.passenger_id == passenger_id,
                RideDB.status == RideDB.RideStatusEnum.IN_PROGRESS,
            )
        )
        return results.scalar_one_or_none() is not None

    async def get_by_id(self, ride_id: str) -> Optional[Ride]:
        result = await self.db.execute(select(RideDB).where(RideDB.id == ride_id))
        ride = result.scalar_one_or_none()
        if ride is None:
            return None
        timestamp = Timestamp()
        timestamp.FromDatetime(ride.requested_at)
        return orm_to_proto_ride(ride, timestamp)

    async def create_ride(self, request: RideRequest) -> str: ...

    async def update_ride(self, ride: Ride) -> None: ...


def orm_to_proto_ride(ride: RideDB, timestamp: Timestamp) -> Ride:
    return Ride(
        ride_id=ride.id,
        ride_request=RideRequest(
            passenger_id=ride.passenger_id,
            from_lat=ride.from_lat,
            from_long=ride.from_long,
            to_lat=ride.to_lat,
            to_long=ride.to_long,
            requested_at=timestamp,
        ),
        driver_id=ride.driver_id,
        accepted_at=ride.accepted_at,
        finished_at=ride.finished_at,
        status=ride.status.value if ride.status else None,
    )


def proto_to_orm_ride(ride):
    pass
