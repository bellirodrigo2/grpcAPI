from datetime import datetime
from uuid import uuid4

from example.guber.server.domain import Coord, Ride, RideStatus
from example.guber.server.domain.service.farecalc import create_fare_calculator
from example.guber.server.domain.vo.segment import Segment


def make_ride_id() -> str:
    return str(uuid4())


def accept_ride(ride: Ride, driver_id: str) -> None:
    if ride.status != RideStatus.REQUESTED:
        raise ValueError(
            f"Invalid status to accept ride: {RideStatus.Name(ride.status)}"
        )
    if ride.HasField("accepted_at"):
        raise ValueError(f"Can´t accept a ride with accepted_at '{ride.accepted_at}'")

    ride.driver_id = driver_id
    ride.status = RideStatus.ACCEPTED
    ride.accepted_at = datetime.now()


def start_ride(ride: Ride) -> None:
    if ride.status != RideStatus.ACCEPTED:
        raise ValueError(
            f"Invalid status to start ride: {RideStatus.Name(ride.status)}"
        )

    if not ride.HasField("accepted_at"):
        raise ValueError(
            f'Can´t start ride: Status without accepted_at time: "{ride.accepted_at}"'
        )

    ride.status = RideStatus.IN_PROGRESS


def update_position(
    ride: Ride,
    last_position: Coord,
    curr_position: Coord,
) -> None:
    if ride.status != RideStatus.IN_PROGRESS:
        raise ValueError(
            f"Invalid status to update position: {RideStatus.Name(ride.status)}"
        )
    segment = Segment(
        last_position,
        curr_position,
    )
    date = ride.accepted_at.ToDatetime()
    additional_fare = create_fare_calculator(date).calculate(segment.distance)
    ride.fare += additional_fare


def finish_ride(ride: Ride) -> None:
    if ride.status != RideStatus.IN_PROGRESS:
        raise ValueError(
            f"Invalid status to finish ride: {RideStatus.Name(ride.status)}"
        )
    ride.status = RideStatus.COMPLETED
    ride.finished_at.FromDatetime(datetime.now())
