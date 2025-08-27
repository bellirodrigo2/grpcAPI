import argparse
from datetime import datetime

import grpc

from example.guber.client.channel import get_channel
from example.guber.server.domain import Coord, Position
from grpcAPI.protobuf import Empty


def main(channel: grpc.Channel, ride_id: str, lat: float, lon: float) -> None:
    method_name = "/ride.ride_actions/update_position"
    stub = channel.unary_unary(
        method_name,
        request_serializer=Position.SerializeToString,
        response_deserializer=Empty.FromString,
        _registered_method=True,
    )
    request = Position(ride_id=ride_id, coord=Coord(lat=lat, long=lon))
    request.updated_at.FromDatetime(datetime.now())

    resp = stub(request)
    print(f"Ride {ride_id} position updated")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--ride_id", type=str, required=True, help="Ride ID")
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude")
    args = parser.parse_args()

    with get_channel() as channel:
        main(channel=channel, ride_id=args.ride_id, lat=args.lat, lon=args.lon)
