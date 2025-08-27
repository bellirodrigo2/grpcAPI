import argparse

import grpc

from example.guber.client.channel import get_channel
from grpcAPI.protobuf import Empty, StringValue


def main(
    channel: grpc.Channel,
    ride_id: str,
) -> None:
    method_name = "/ride.ride_actions/start_ride"
    stub = channel.unary_unary(
        method_name,
        request_serializer=StringValue.SerializeToString,
        response_deserializer=Empty.FromString,
        _registered_method=True,
    )
    request = StringValue(value=ride_id)
    resp = stub(request)
    print(f"Ride {ride_id} started")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--ride_id", type=str, required=True, help="Ride ID")
    args = parser.parse_args()

    with get_channel() as channel:
        main(channel=channel, ride_id=args.ride_id)
