import grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc


def list_services(channel):
    stub = reflection_pb2_grpc.ServerReflectionStub(channel)
    request = reflection_pb2.ServerReflectionRequest(list_services="")

    response_stream = stub.ServerReflectionInfo(iter([request]))
    for response in response_stream:
        services = response.list_services_response.service
        print("Available services via reflection:")
        for svc in services:
            print(f" - {svc.name}")


def main():
    target = "localhost:50051"
    with grpc.insecure_channel(target) as channel:
        list_services(channel)


if __name__ == "__main__":
    main()
