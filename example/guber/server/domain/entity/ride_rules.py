from typing import Tuple

from example.guber.server.domain import Ride, RideStatus
from example.guber.server.domain.service.farecalc import create_fare_calculator
from example.guber.server.domain.vo.segment import Segment
from grpcAPI.protobuf import Timestamp


def accept_ride(ride: Ride, driver_id: str) -> None:

    if ride.status != RideStatus.REQUESTED:
        raise ValueError("Invalid status")
    if ride.accepted_at is not None:
        raise ValueError(
            f"Inconsistent Ride: Status '{ride.status}' with accepted_at '{ride.accepted_at}'"
        )

    ride.driver_id = driver_id
    ride.status = RideStatus.ACCEPTED
    ts_now = Timestamp()
    ts_now.GetCurrentTime()
    ride.accepted_at = ts_now


def start_ride(ride: Ride) -> None:
    if ride.status != RideStatus.ACCEPTED:
        raise ValueError("Invalid status")


def update_position(
    ride: Ride,
    last_position: Tuple[float, float],
    curr_position: Tuple[float, float],
) -> None:
    if ride.status != RideStatus.IN_PROGRESS:
        raise ValueError("Invalid status")
    last_lat, last_long = last_position
    curr_lat, curr_long = curr_position
    segment = Segment(
        (last_lat, last_long),
        (curr_lat, curr_long),
    )
    date = ride.accepted_at.ToDatetime()
    additional_fare = create_fare_calculator(date).calculate(segment.distance)
    ride.fare += additional_fare


def finish_ride(ride: Ride) -> None:
    if ride.status != RideStatus.IN_PROGRESS:
        raise ValueError("Invalid status")
    ride.status = RideStatus.COMPLETED
