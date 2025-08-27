import argparse

import grpc

from example.guber.client.channel import get_channel
from example.guber.server.domain import Account
from grpcAPI.protobuf import StringValue


def main(channel: grpc.Channel, id: str) -> None:
    method_name = "/account.account_services/get_account"
    stub = channel.unary_unary(
        method_name,
        request_serializer=StringValue.SerializeToString,
        response_deserializer=Account.FromString,
        _registered_method=True,
    )
    request = StringValue(value=id)
    account = stub(request)
    print(account)


if __name__ == "__main__":
    id = "28c9eb17-60e8-44f0-9619-f9dedf56463e"
    # id2 = "820b98e6-89d1-4aa1-8b19-cc16e68f48f8"

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--id", type=str, default=id, help="Account ID")
    args = parser.parse_args()

    with get_channel() as channel:
        main(channel=channel, id=args.id)
