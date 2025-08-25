import pytest

from example.guber.server.application.usecase.account import (
    get_account,
    is_passenger,
    signup_account,
    update_car_plate,
    update_email,
)
from example.guber.server.application.usecase.ride import (
    accept_ride,
    finish_ride,
    get_position_stream,
    get_ride,
    request_ride,
    start_ride,
    update_position,
    update_position_stream,
)
from example.guber.tests.helpers import (
    create_passenger_info,
    create_position,
    create_ride_request,
    get_unique_email,
    get_unique_sin,
)
from grpcAPI.protobuf import StringValue
from grpcAPI.protobuf.lib.prototypes_pb2 import KeyValueStr
from grpcAPI.testclient import TestClient
from grpcAPI.testclient.contextmock import ContextMock


@pytest.fixture
def get_mock_no_auth_context():
    context = ContextMock()
    return context


# Account service authentication failure tests
async def test_signup_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 6), sin=get_unique_sin(2)
    )

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=signup_account,
            request=passenger_info,
            context=get_mock_no_auth_context,
        )


async def test_get_account_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    account_id = StringValue(value="test_account_id")

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=get_account,
            request=account_id,
            context=get_mock_no_auth_context,
        )


async def test_update_car_plate_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):

    request = KeyValueStr(key="id_uniqueee", value="ABC-1234")
    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=update_car_plate,
            request=request,
            context=get_mock_no_auth_context,
        )


async def test_update_email_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    request = KeyValueStr(key="id_uniqueee123", value="emailtest@email.com.br")
    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=update_email,
            request=request,
            context=get_mock_no_auth_context,
        )


async def test_is_passenger_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    account_id = StringValue(value="test_passenger_id")

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=is_passenger,
            request=account_id,
            context=get_mock_no_auth_context,
        )


# Ride service authentication failure tests
async def test_request_ride_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    ride_request = create_ride_request(passenger_id="test_passenger_id")

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=request_ride,
            request=ride_request,
            context=get_mock_no_auth_context,
        )


async def test_accept_ride_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):

    request = KeyValueStr(key="unique_ride_id", value="unique_drive_id")
    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=accept_ride,
            request=request,
            context=get_mock_no_auth_context,
        )


async def test_get_ride_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    ride_id = StringValue(value="test_ride_id")

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=get_ride,
            request=ride_id,
            context=get_mock_no_auth_context,
        )


async def test_start_ride_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    ride_id = StringValue(value="test_ride_id")

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=start_ride,
            request=ride_id,
            context=get_mock_no_auth_context,
        )


async def test_update_position_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    position = create_position("test_ride_id", -27.584905, -48.545022)

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=update_position,
            request=position,
            context=get_mock_no_auth_context,
        )


async def test_finish_ride_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    ride_id = StringValue(value="test_ride_id")

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=finish_ride,
            request=ride_id,
            context=get_mock_no_auth_context,
        )


async def test_update_position_stream_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    position = create_position("test_ride_id", -27.584905, -48.545022)

    with pytest.raises(ValueError, match="Invalid metadata"):
        await app_test_client.run(
            func=update_position_stream,
            request=position,
            context=get_mock_no_auth_context,
        )


async def test_get_position_stream_no_auth(
    app_test_client: TestClient,
    get_mock_no_auth_context: ContextMock,
):
    ride_id = StringValue(value="test_ride_id")

    with pytest.raises(ValueError, match="Invalid metadata"):
        # For async generator functions, we need to trigger the generator execution
        async_generator = await app_test_client.run(
            func=get_position_stream,
            request=ride_id,
            context=get_mock_no_auth_context,
        )
        # Try to get the first item from the async generator to trigger authentication
        await async_generator.__anext__()
