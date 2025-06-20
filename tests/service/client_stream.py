import sys
from pathlib import Path

import grpc

source_folder = Path(__file__).parent.parent
sys.path.append(str(source_folder / "proto2" / "compiled"))

from tests.proto2.compiled import service_pb2, service_pb2_grpc


def run() -> None:
    # 1) Cria canal síncrono
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = service_pb2_grpc.user_serviceStub(channel)

        # 2) Prepara lista de requests
        requests = [
            service_pb2.user_input(
                code=service_pb2.EMPLOYEE,
                age=28,
                name="Alice",
                affilliation="ACME Corp",
            ),
            service_pb2.user_input(
                code=service_pb2.SCHOOL,
                age=22,
                name="Bob",
                affilliation="UniX University",
            ),
            service_pb2.user_input(
                code=service_pb2.INACTIVE, age=45, name="Charlie", affilliation=""
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
