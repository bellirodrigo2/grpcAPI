import asyncio
from datetime import datetime
from typing import List, Tuple

import grpc

from example.guber.server.domain import Coord, Position
from grpcAPI.protobuf import Empty


async def update_position_stream(
    channel: grpc.Channel,
    ride_id: str,
    positions: List[Tuple[float, float]],
    delay: float,
) -> None:
    method_name = "/ride.ride_actions/update_position_stream"
    stub = channel.stream_unary(
        method_name,
        request_serializer=Position.SerializeToString,
        response_deserializer=Empty.FromString,
        _registered_method=True,
    )

    async def position_generator():
        for lat, long in positions:
            request = Position(ride_id=ride_id, coord=Coord(lat=lat, long=long))
            request.updated_at.FromDatetime(datetime.now())
            print(f"Updating position: for {ride_id} to ({lat}, {long})")
            yield request
            await asyncio.sleep(delay)

    await stub(position_generator())
