import sys
from pathlib import Path

import grpc

from grpcAPI.proto_load import import_modules

p = Path(__file__).parent / "proto"
modules = import_modules(p, ["compiled"])
from example.userpack.proto.compiled.pack1 import mod1_pb2
from example.userpack.proto.compiled.pack2 import mod2_pb2_grpc


def run() -> None:
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = mod2_pb2_grpc.user_serviceStub(channel)

        # Cria a requisição com os IDs
        request = mod1_pb2.UserNames(ids=[1, 2, 3, 4])

        # Chama o método que retorna um stream
        response_iterator = stub.getusers(request)

        print("Usuários recebidos:")
        for user in response_iterator:
            print(
                f"ID: {user.id}, Nome: {user.name}, Idade: {user.age}, Inativo: {user.inactive}"
            )


if __name__ == "__main__":
    run()
