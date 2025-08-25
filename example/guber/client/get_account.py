import argparse

import grpc

from example.guber.server.domain import Account
from grpcAPI.protobuf import StringValue


def main(id: str) -> None:
    with grpc.insecure_channel("localhost:50051") as channel:
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

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument("--id", type=str, default=id, help="Account ID")
    args = parser.parse_args()

    main(args.id)
