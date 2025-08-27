import argparse

import grpc

from example.guber.client.channel import get_channel
from grpcAPI.protobuf import BoolValue, KeyValueStr


def update_car_plate(channel: grpc.Channel, id: str, car_plate: str) -> bool:
    method_name = "/account.account_services/update_car_plate"
    stub = channel.unary_unary(
        method_name,
        request_serializer=KeyValueStr.SerializeToString,
        response_deserializer=BoolValue.FromString,
        _registered_method=True,
    )
    request = KeyValueStr(key=id, value=car_plate)
    resp = stub(request)
    if resp.value:
        print("Car Plate Updated Successfully")
        return True
    else:
        print("Car Plate Update Failed")
        return False


if __name__ == "__main__":
    id = "28c9eb17-60e8-44f0-9619-f9dedf56463e"

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--id", type=str, default=id, help="Account ID")
    parser.add_argument("--plate", type=str, required=True, help="New car plate")
    args = parser.parse_args()

    with get_channel() as channel:
        update_car_plate(channel=channel, id=args.id, car_plate=args.plate)
