import sys
from pathlib import Path

from typing_extensions import Annotated, Any, Callable, Optional

from grpcAPI.data_types import FromRequest

lib_path = Path(".") / "example/guber/lib"
print(lib_path)
sys.path.insert(0, str(lib_path.resolve()))
from example.guber.lib.account.account_proto_pb2 import Account, AccountInfo
from example.guber.lib.keyvalue_pb2 import KeyValueStr
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


class FromKey(FromRequest):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=KeyValueStr, field="key", validator=validator, **meta)


class FromValue(FromRequest):
    def __init__(self, validator: Optional[Callable[..., Any]] = None, **meta: Any):
        super().__init__(model=KeyValueStr, field="value", validator=validator, **meta)


ProtoKey = Annotated[str, FromKey()]
ProtoValue = Annotated[str, FromValue()]


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
    "KeyValueStr",
    "ProtoKey",
    "ProtoValue",
    "FromKey",
    "FromValue",
]
