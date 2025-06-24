from pathlib import Path

import grpc

from grpcAPI.module_import import import_modules

p = Path(__file__).parent / "proto"
modules = import_modules(p, ["compiled"])
from example.userpack.proto.compiled.pack1 import mod1_pb2
from example.userpack.proto.compiled.pack2 import mod2_pb2_grpc


def run() -> None:
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = mod2_pb2_grpc.user_serviceStub(channel)
        request = mod1_pb2.UserInput(
            code=mod1_pb2.EMPLOYEE, age=30, name="John Doe", affilliation="ACME Corp"
        )
        response = stub.newuser(request)

        print("Resposta recebida:")
        print(response)


if __name__ == "__main__":
    run()
