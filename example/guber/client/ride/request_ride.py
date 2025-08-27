import argparse
import asyncio

import grpc

from example.guber.client.channel import get_async_channel
from example.guber.server.domain import RideRequest
from grpcAPI.protobuf import StringValue


async def request_ride(channel: grpc.Channel, passenger_id: str) -> str:
    method_name = "/ride.user_ride_actions/request_ride"
    stub = channel.unary_unary(
        method_name,
        request_serializer=RideRequest.SerializeToString,
        response_deserializer=StringValue.FromString,
        _registered_method=True,
    )
    request = RideRequest(passenger_id=passenger_id)
    ride = await stub(request)
    print(ride)
    return ride.value


if __name__ == "__main__":
    # id = "28c9eb17-60e8-44f0-9619-f9dedf56463e"
    id = "820b98e6-89d1-4aa1-8b19-cc16e68f48f8"

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--id", type=str, default=id, help="Account ID")
    args = parser.parse_args()

    async def run():
        async with get_async_channel(port="50052") as channel:
            await request_ride(channel=channel, passenger_id=args.id)

    asyncio.run(run())
