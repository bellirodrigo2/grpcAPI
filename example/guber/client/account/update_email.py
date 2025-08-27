import argparse

import grpc

from example.guber.client.channel import get_channel
from grpcAPI.protobuf import BoolValue, KeyValueStr


def update_email(channel: grpc.Channel, id: str, email: str) -> bool:
    method_name = "/account.account_services/update_email"
    stub = channel.unary_unary(
        method_name,
        request_serializer=KeyValueStr.SerializeToString,
        response_deserializer=BoolValue.FromString,
        _registered_method=True,
    )
    request = KeyValueStr(key=id, value=email)
    resp = stub(request)
    if resp.value:
        print("Email Updated Successfully")
        return True
    else:
        print("Email Update Failed")
        return False


if __name__ == "__main__":
    id = "28c9eb17-60e8-44f0-9619-f9dedf56463e"

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--id", type=str, default=id, help="Account ID")
    parser.add_argument("--email", type=str, required=True, help="New email address")
    args = parser.parse_args()

    with get_channel() as channel:
        update_email(channel=channel, id=args.id, email=args.email)
