import argparse
import asyncio

import grpc

from example.guber.client.channel import get_async_channel
from example.guber.server.domain import RideSnapshot
from grpcAPI.protobuf import StringValue


async def get_ride(channel: grpc.Channel, ride_id: str) -> RideSnapshot:
    method_name = "/ride.ride_actions/get_ride"
    stub = channel.unary_unary(
        method_name,
        request_serializer=StringValue.SerializeToString,
        response_deserializer=RideSnapshot.FromString,
        _registered_method=True,
    )
    request = StringValue(value=ride_id)
    ride_snapshot = await stub(request)
    print(ride_snapshot)
    return ride_snapshot


if __name__ == "__main__":
    id = "271aee50-2276-4494-99cb-0fa076ce580e"
    # id2 = "820b98e6-89d1-4aa1-8b19-cc16e68f48f8"

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--id", type=str, default=id, help="Account ID")
    args = parser.parse_args()

    async def run():
        async with get_async_channel() as channel:
            get_ride(channel=channel, ride_id=args.id)

    asyncio.run(run())
