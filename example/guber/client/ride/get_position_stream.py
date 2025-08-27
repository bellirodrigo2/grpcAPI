import grpc

from example.guber.server.domain import Position
from grpcAPI.protobuf import StringValue


async def get_position_stream(
    channel: grpc.Channel, ride_id: str, delay: float, counter: int
) -> None:
    method_name = "/ride.ride_actions/get_position_stream"
    stub = channel.unary_stream(
        method_name,
        request_serializer=StringValue.SerializeToString,
        response_deserializer=Position.FromString,
        _registered_method=True,
    )
    metadata = (
        ("counter", str(counter)),
        ("delay", str(delay)),
    )
    async for position in stub(StringValue(value=ride_id), metadata=metadata):
        print(f"Received position update for {ride_id}: {position}")
