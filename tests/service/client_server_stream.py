import sys
from pathlib import Path

import grpc

# Configuração de path para os stubs gerados
source_folder = Path(__file__).parent.parent
p = source_folder / "proto2" / "compiled"
sys.path.append(str(p))

# Importação dos stubs gerados
from tests.proto2.compiled import service_pb2, service_pb2_grpc


def run() -> None:
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = service_pb2_grpc.user_serviceStub(channel)

        # Cria a requisição com os IDs
        request = service_pb2.names_id(ids=[1, 2, 3, 4])

        # Chama o método que retorna um stream
        response_iterator = stub.getusers(request)

        print("Usuários recebidos:")
        for user in response_iterator:
            print(
                f"ID: {user.id}, Nome: {user.name}, Idade: {user.age}, Inativo: {user.inactive}"
            )


if __name__ == "__main__":
    run()
