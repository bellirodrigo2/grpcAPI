import grpc

from tests.proto2.compiled import service_pb2, service_pb2_grpc


def run() -> None:
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = service_pb2_grpc.user_serviceStub(channel)
        request = service_pb2.user_input(
            code=service_pb2.EMPLOYEE, age=30, name="John Doe", affilliation="ACME Corp"
        )

        response = stub.newuser(request)

        print("Resposta recebida:")
        print(response)


if __name__ == "__main__":
    run()
