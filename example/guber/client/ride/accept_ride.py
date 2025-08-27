import argparse
import asyncio

import grpc

from example.guber.client.channel import get_async_channel
from grpcAPI.protobuf import Empty, KeyValueStr


async def accept_ride(channel: grpc.Channel, ride_id: str, driver_id: str) -> None:
    method_name = "/ride.driver_ride_actions/accept_ride"
    stub = channel.unary_unary(
        method_name,
        request_serializer=KeyValueStr.SerializeToString,
        response_deserializer=Empty.FromString,
        _registered_method=True,
    )
    request = KeyValueStr(key=ride_id, value=driver_id)
    await stub(request)
    print(f"Ride {ride_id} accepted by driver {driver_id}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--ride_id", type=str, required=True, help="Ride ID")
    parser.add_argument("--driver_id", type=str, required=True, help="Driver ID")
    args = parser.parse_args()

    async def run():
        async with get_async_channel() as channel:
            await accept_ride(
                channel=channel, ride_id=args.ride_id, driver_id=args.driver_id
            )

    asyncio.run(run())
