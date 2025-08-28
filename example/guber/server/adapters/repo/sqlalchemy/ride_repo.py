from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import select
from typing_extensions import Optional

from example.guber.server.adapters.repo.sqlalchemy import (
    AsyncSessionLocal,
    RideDB,
    RideDBStatus,
    SqlAlchemyDB,
)
from example.guber.server.application.repo import RideRepo
from example.guber.server.domain import Coord, Ride, RideRequest, RideStatus


class SqlAlchemyRideRepo(SqlAlchemyDB, RideRepo):

    async def has_active_ride_by_passenger(self, passenger_id: str) -> bool:
        return await self._has_active_ride(passenger_id, "passenger")

    async def has_active_ride_by_driver(self, driver_id: str) -> bool:
        return await self._has_active_ride(driver_id, "driver")

    async def _has_active_ride(self, passenger_id: str, user: str) -> bool:
        if user == "driver":
            tgtuser = RideDB.driver_id
        else:
            tgtuser = RideDB.passenger_id
        result = await self.db.execute(
            select(RideDB)
            .where(
                tgtuser == passenger_id,
            )
            .where(
                RideDB.status.in_(
                    [
                        RideDBStatus.REQUESTED,
                        RideDBStatus.ACCEPTED,
                        RideDBStatus.IN_PROGRESS,
                    ]
                )
            )
        )
        return result.scalars().first() is not None

    async def get_by_ride_id(self, ride_id: str) -> Optional[Ride]:
        result = await self.db.execute(select(RideDB).where(RideDB.ride_id == ride_id))
        ride = result.scalar_one_or_none()

        return orm_to_proto(ride)

    async def create_ride(self, id: str, request: RideRequest) -> str:
        ride_id = id

        ride_db = RideDB(
            ride_id=ride_id,
            passenger_id=request.passenger_id,
            driver_id="",  # No driver assigned initially
            start_lat=request.start_point.lat,
            start_long=request.start_point.long,
            end_lat=request.end_point.lat,
            end_long=request.end_point.long,
            fare=0.0,  # Initial fare is 0
            status=RideDBStatus.REQUESTED,
            accepted_at=None,
            finished_at=None,
        )

        self.db.add(ride_db)
        await self.db.commit()
        return ride_id

    async def update_ride(self, ride: Ride) -> None:
        result = await self.db.execute(
            select(RideDB).where(RideDB.ride_id == ride.ride_id)
        )
        ride_db = result.scalar_one_or_none()

        if ride_db is None:
            raise ValueError(f"Ride with id {ride.ride_id} not found")

        # Update fields
        ride_db.passenger_id = ride.passenger_id
        ride_db.driver_id = ride.driver_id
        ride_db.start_lat = ride.start_point.lat
        ride_db.start_long = ride.start_point.long
        ride_db.end_lat = ride.end_point.lat
        ride_db.end_long = ride.end_point.long
        ride_db.fare = ride.fare
        ride_db.status = proto_status_to_db_status(ride.status)
        if ride.HasField("accepted_at"):
            ride_db.accepted_at = ride.accepted_at.ToDatetime()
        if ride.HasField("finished_at"):
            ride_db.finished_at = ride.finished_at.ToDatetime()

        await self.db.commit()

    async def is_ride_finished(self, ride_id: str) -> bool:
        result = await self.db.execute(
            select(RideDB.status).where(RideDB.ride_id == ride_id)
        )
        status = result.scalar_one_or_none()

        if status is None:
            return False  # Ride doesn't exist

        return status in [RideDBStatus.COMPLETED, RideDBStatus.CANCELED]


@asynccontextmanager
async def get_ride_sqlalchemy_repo() -> AsyncGenerator[RideRepo, None]:  # type: ignore
    db = AsyncSessionLocal()
    try:
        # Establish connection right before use
        await db.connection()
        yield SqlAlchemyRideRepo(db)
    finally:
        await db.close()


def proto_status_to_db_status(proto_status: RideStatus.ValueType) -> RideDBStatus:
    status_name = RideStatus.Name(proto_status)
    return RideDBStatus[status_name]


def orm_to_proto(ride: Optional[RideDB]) -> Optional[Ride]:
    if ride is None:
        return None
    from_coord = Coord(lat=ride.start_lat, long=ride.start_long)
    to_coord = Coord(lat=ride.end_lat, long=ride.end_long)
    status_val = RideStatus.Value(ride.status.name)
    ride_obj = Ride(
        ride_id=ride.ride_id,
        passenger_id=ride.passenger_id,
        driver_id=ride.driver_id if ride.driver_id else "",
        start_point=from_coord,
        end_point=to_coord,
        fare=ride.fare,
        status=RideStatus.Name(status_val),
        accepted_at=ride.accepted_at,
        finished_at=ride.finished_at,
    )
    return ride_obj
