from grpcAPI import APIService, GrpcAPI
from grpcAPI.protobuf import BytesValue, StringValue

app = GrpcAPI()

service = APIService("service1")


@service
async def my_service(
    strvalue: StringValue,
    bytesvalue: BytesValue,  # two diferent request protobuf objects
) -> StringValue:  # no return type annotation
    pass


@service
async def my_service2(
    bytesvalue: BytesValue,  # two diferent request protobuf objects
):  # no return type annotation
    pass


app.add_service(service)

# grpcapi lint .\server\malformedapp.py
