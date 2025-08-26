import argparse

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from example.guber.client.channel import get_channel


def main(channel: grpc.Channel, service_name: str) -> None:
    stub = health_pb2_grpc.HealthStub(channel)
    request = health_pb2.HealthCheckRequest(service=service_name)
    response = stub.Check(request)
    print(f"Health status for '{service_name or 'ALL'}': {response}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="gRPC Health Check Client")
    parser.add_argument(
        "--service", "-s", default="", help="Nome do serviço a ser verificado"
    )
    args = parser.parse_args()
    with get_channel() as channel:
        main(channel, args.service)
