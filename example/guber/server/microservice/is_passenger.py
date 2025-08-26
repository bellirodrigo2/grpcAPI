from pathlib import Path

from example.guber.client.channel import get_async_channel
from grpcAPI.commands.settings.utils import load_file_by_extension
from grpcAPI.protobuf import BoolValue, StringValue

MICROSERVICE_PATH = Path(__file__).parent / "account.config.json"
guber_settings = load_file_by_extension(MICROSERVICE_PATH)

ACCOUNT_HOST = guber_settings.get("host", "localhost")
ACCOUNT_PORT = str(guber_settings.get("port", 50051))


def is_passenger_client():
    async def is_passenger_client_(id: str) -> bool:

        async with get_async_channel(ACCOUNT_HOST, ACCOUNT_PORT) as channel:
            method_name = "/account.account_services/is_passenger"
            stub = channel.unary_unary(
                method_name,
                request_serializer=StringValue.SerializeToString,
                response_deserializer=BoolValue.FromString,
            )
            request = StringValue(value=id)
            response = await stub(request)
            return response.value

    return is_passenger_client_
