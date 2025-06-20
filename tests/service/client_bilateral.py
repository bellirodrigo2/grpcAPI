import sys
import time
from pathlib import Path

import grpc

source_folder = Path(__file__).parent.parent
sys.path.append(str(source_folder / "proto2" / "compiled"))


from tests.proto2.compiled import service_pb2, service_pb2_grpc


def generate_requests():
    users = [
        service_pb2.user_input(
            code=service_pb2.EMPLOYEE,
            age=35,
            name="Diana",
            affilliation="Globex",
        ),
        service_pb2.user_input(
            code=service_pb2.SCHOOL,
            age=20,
            name="Evan",
            affilliation="Springfield College",
        ),
        service_pb2.user_input(
            code=service_pb2.INACTIVE,
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
        stub = service_pb2_grpc.user_serviceStub(channel)

        responses = stub.bilateralnewuser(generate_requests())

        print("Respostas recebidas:")
        for resp in responses:
            occ = resp.WhichOneof("occupation")
            val = getattr(resp, occ)
            print(f" • id={resp.id}, name={resp.name}, age={resp.age}, {occ}={val}")


if __name__ == "__main__":
    run()
