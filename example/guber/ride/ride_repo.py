# export default interface RideRepository {
# 	saveRide (ride: Ride): Promise<void>;
# 	getRideById (rideId: string): Promise<Ride>;
# 	hasActiveRideByPassengerId (passengerId: string): Promise<boolean>;
# }

from typing import Optional

from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy.orm import Session

from example.guber.lib.ride.ride_proto_pb2 import RideInfo, RideRequest
from example.guber.models.ride import Ride


async def get_by_id(id: str, db: Session) -> Optional[RideInfo]:
    ride = db.query(Ride).filter(Ride.id == id).first()
    if ride is None:
        return None
    timestamp = Timestamp()
    timestamp.FromDatetime(ride.requested_at)
    ride_request = RideRequest(
        passenger_id=ride.passenger_id,
        from_lat=ride.from_lat,
        from_long=ride.from_long,
        to_lat=ride.to_lat,
        to_long=ride.to_long,
        requested_at=timestamp,
    )
    return RideInfo(
        driver_id=ride.driver_id,
        ride_request=ride_request,
        ride_id=ride.id,
        accepted_at=ride.accepted_at,
        finished_at=ride.finished_at,
        status=ride.status.value if ride.status else None,
    )


async def get_active_ride_by_passenger_id(
    passenger_id: str, db: Session
) -> Optional[Ride]:
    return (
        db.query(Ride)
        .filter(
            Ride.passenger_id == passenger_id,
            Ride.status == Ride.RideStatusEnum.IN_PROGRESS,
        )
        .first()
    )


async def save_ride(ride: RideInfo, db: Session) -> None:
    ride_model = Ride(
        id=ride.ride_id,
        passenger_id=ride.ride_request.passenger_id,
        from_lat=ride.ride_request.from_lat,
        from_long=ride.ride_request.from_long,
        to_lat=ride.ride_request.to_lat,
        to_long=ride.ride_request.to_long,
        requested_at=ride.ride_request.requested_at.ToDatetime(),
        driver_id=ride.driver_id,
        accepted_at=ride.accepted_at.ToDatetime() if ride.accepted_at else None,
        finished_at=ride.finished_at.ToDatetime() if ride.finished_at else None,
        status=Ride.RideStatusEnum(ride.status) if ride.status else None,
    )
    db.add(ride_model)
    db.commit()
    db.refresh(ride_model)
