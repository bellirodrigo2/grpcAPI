import grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc

from example.guber.client.channel import get_channel


def list_services(channel: grpc.Channel) -> None:
    stub = reflection_pb2_grpc.ServerReflectionStub(channel)
    request = reflection_pb2.ServerReflectionRequest(list_services="")

    response_stream = stub.ServerReflectionInfo(iter([request]))
    for response in response_stream:
        services = response.list_services_response.service
        print("Available services via reflection:")
        for svc in services:
            print(f" - {svc.name}")


if __name__ == "__main__":

    with get_channel() as channel:
        list_services(channel)
