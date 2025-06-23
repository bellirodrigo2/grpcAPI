import sys
from pathlib import Path

import grpc

from grpcAPI.module_import import import_modules

p = Path(__file__).parent / "proto"
modules = import_modules(p, ["compiled"])
from example.userpack.proto.compiled.pack1 import mod1_pb2
from example.userpack.proto.compiled.pack2 import mod2_pb2_grpc


def run() -> None:
    # 1) Cria canal síncrono
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = mod2_pb2_grpc.user_serviceStub(channel)

        # 2) Prepara lista de requests
        requests = [
            mod1_pb2.UserInput(
                code=mod1_pb2.EMPLOYEE,
                age=28,
                name="Alice",
                affilliation="ACME Corp",
            ),
            mod1_pb2.UserInput(
                code=mod1_pb2.SCHOOL,
                age=22,
                name="Bob",
                affilliation="UniX University",
            ),
            mod1_pb2.UserInput(
                code=mod1_pb2.INACTIVE, age=45, name="Charlie", affilliation=""
            ),
        ]

        # 3) Chama manynewuser passando um iterável
        response = stub.manynewuser(iter(requests))

        # 4) Mostra resultado
        print("Resposta recebida (user_list):")
        for u in response.users:
            occ = u.WhichOneof("occupation")
            val = getattr(u, occ)
            print(f" • id={u.id}, name={u.name}, age={u.age}, {occ}={val}")


if __name__ == "__main__":
    run()
