import argparse

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc


def check_health(channel, service_name):
    stub = health_pb2_grpc.HealthStub(channel)
    request = health_pb2.HealthCheckRequest(service=service_name)
    response = stub.Check(request)
    print(f"Health status for '{service_name or 'ALL'}': {response}")


def main(service: str):
    target = "localhost:50051"  # altere para o endereço do seu servidor
    with grpc.insecure_channel(target) as channel:
        check_health(channel, service)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gRPC Health Check Client")
    parser.add_argument(
        "--service", default="", help="Nome do serviço a ser verificado"
    )
    args = parser.parse_args()
    main(args.service)
