import sys
import time
from pathlib import Path

import grpc

from grpcAPI.proto_load import import_modules

p = Path(__file__).parent / "proto"
modules = import_modules(p, ["compiled"])
from example.userpack.proto.compiled.pack1 import mod1_pb2
from example.userpack.proto.compiled.pack2 import mod2_pb2_grpc


def generate_requests():
    users = [
        mod1_pb2.UserInput(
            code=mod1_pb2.EMPLOYEE,
            age=35,
            name="Diana",
            affilliation="Globex",
        ),
        mod1_pb2.UserInput(
            code=mod1_pb2.SCHOOL,
            age=20,
            name="Evan",
            affilliation="Springfield College",
        ),
        mod1_pb2.UserInput(
            code=mod1_pb2.INACTIVE,
            age=50,
            name="Frank",
            affilliation="",  # Inativo não requer affilliation textual
        ),
    ]
    for user in users:
        print(f"Enviando: {user.name}")
        yield user
        time.sleep(0.5)  # Simula latência ou entrada gradual


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = mod2_pb2_grpc.user_serviceStub(channel)

        responses = stub.bilateralnewuser(generate_requests())

        print("Respostas recebidas:")
        for resp in responses:
            occ = resp.WhichOneof("occupation")
            val = getattr(resp, occ)
            print(f" • id={resp.id}, name={resp.name}, age={resp.age}, {occ}={val}")


if __name__ == "__main__":
    run()
