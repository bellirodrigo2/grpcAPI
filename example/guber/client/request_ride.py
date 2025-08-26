import argparse

import grpc

from example.guber.client.channel import get_channel
from example.guber.server.domain import RideRequest
from grpcAPI.protobuf import StringValue


def main(channel: grpc.Channel, passenger_id: str) -> None:
    method_name = "/ride.user_ride_actions/request_ride"
    stub = channel.unary_unary(
        method_name,
        request_serializer=RideRequest.SerializeToString,
        response_deserializer=StringValue.FromString,
        _registered_method=True,
    )
    request = RideRequest(passenger_id=passenger_id)
    ride = stub(request)
    print(ride)


if __name__ == "__main__":
    # id = "28c9eb17-60e8-44f0-9619-f9dedf56463e"
    id = "820b98e6-89d1-4aa1-8b19-cc16e68f48f8"

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--id", type=str, default=id, help="Account ID")
    args = parser.parse_args()

    with get_channel(port=50052) as channel:
        main(channel=channel, passenger_id=args.id)
