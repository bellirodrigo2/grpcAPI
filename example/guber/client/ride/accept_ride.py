import argparse

import grpc

from example.guber.client.channel import get_channel
from grpcAPI.protobuf import Empty, KeyValueStr


def main(channel: grpc.Channel, ride_id: str, driver_id: str) -> None:
    method_name = "/ride.driver_ride_actions/accept_ride"
    stub = channel.unary_unary(
        method_name,
        request_serializer=KeyValueStr.SerializeToString,
        response_deserializer=Empty.FromString,
        _registered_method=True,
    )
    request = KeyValueStr(key=ride_id, value=driver_id)
    resp = stub(request)
    print(f"Ride {ride_id} accepted by driver {driver_id}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--ride_id", type=str, required=True, help="Ride ID")
    parser.add_argument("--driver_id", type=str, required=True, help="Driver ID")
    args = parser.parse_args()

    with get_channel() as channel:
        main(channel=channel, ride_id=args.ride_id, driver_id=args.driver_id)
