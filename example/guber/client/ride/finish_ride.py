import argparse
import asyncio

import grpc

from example.guber.client.channel import get_async_channel
from grpcAPI.protobuf import Empty, StringValue


async def finish_ride(
    channel: grpc.Channel,
    ride_id: str,
) -> None:
    method_name = "/ride.ride_actions/finish_ride"
    stub = channel.unary_unary(
        method_name,
        request_serializer=StringValue.SerializeToString,
        response_deserializer=Empty.FromString,
        _registered_method=True,
    )
    request = StringValue(value=ride_id)
    await stub(request)
    print(f"Ride {ride_id} finished")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--ride_id", type=str, required=True, help="Ride ID")
    args = parser.parse_args()

    async def run():
        async with get_async_channel() as channel:
            await finish_ride(channel=channel, ride_id=args.ride_id)

    asyncio.run(run())
