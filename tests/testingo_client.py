import grpc
from google.protobuf.wrappers_pb2 import StringValue


def main() -> None:
    with grpc.insecure_channel("localhost:50051") as channel:
        method_name = "/functional/echo"
        echo = channel.unary_unary(
            method_name,
            request_serializer=StringValue.SerializeToString,
            response_deserializer=StringValue.FromString,
            _registered_method=True,
        )
        print(echo(StringValue(value="foo")))


if __name__ == "__main__":
    main()
