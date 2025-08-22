import sys
from pathlib import Path

lib_path = Path(".") / "example/guber/lib"
print(lib_path)
sys.path.insert(0, str(lib_path.resolve()))
from example.guber.lib.account.account_proto_pb2 import Account, AccountInfo
from example.guber.lib.ride.ride_proto_pb2 import (
    Coord,
    Position,
    Ride,
    RideRequest,
    RideSnapshot,
    RideStatus,
)
from example.guber.server.domain.entity.ride_rules import (
    accept_ride,
    finish_ride,
    start_ride,
    update_position,
)
from example.guber.server.domain.vo.account import (
    EmailStr,
    validate_car_plate,
    validate_sin,
)

__all__ = [
    "Ride",
    "RideRequest",
    "RideStatus",
    "RideSnapshot",
    "Position",
    "Account",
    "Coord",
    "AccountInfo",
    "accept_ride",
    "start_ride",
    "update_position",
    "finish_ride",
    "validate_sin",
    "validate_car_plate",
    "EmailStr",
]
