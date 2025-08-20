import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import (
    accept_ride,
    request_ride,
    start_ride,
)
from example.guber.server.domain import AccountInfo, RideRequest, RideStatus
from grpcAPI.protobuf import StringValue
from grpcAPI.protobuf.lib.prototypes_pb2 import KeyValueStr
from grpcAPI.testclient import ContextMock, TestClient

pytest_plugins = ["example.guber.tests.fixtures"]


async def test_start_ride(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create passenger account
    passenger_info = get_account_info
    passenger_info.is_driver = False
    passenger_info.car_plate = ""
    context._is_passenger = True

    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    # Create ride request
    ride_request = get_ride_request
    ride_request.passenger_id = passenger_id

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Create driver account
    driver_info = AccountInfo(
        name="Driver User",
        email="driver@example.com",
        sin="123456782",
        car_plate="DEF-5678",
        is_driver=True,
    )
    context._is_passenger = False  # Switch to driver

    driver_resp = await app_test_client.run(
        func=signup_account,
        request=driver_info,
        context=context,
    )
    driver_id = driver_resp.value

    # Accept the ride
    accept_request = KeyValueStr(key=ride_id, value=driver_id)
    await app_test_client.run(
        func=accept_ride,
        request=accept_request,
        context=context,
    )

    # Start the ride
    await app_test_client.run(
        func=start_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Verify ride was started
    ride_repo = context._mock_ride_repo
    ride = await ride_repo.get_by_ride_id(ride_id)
    assert ride is not None
    assert ride.status == RideStatus.IN_PROGRESS
    assert ride.driver_id == driver_id
    assert ride.HasField("accepted_at")


async def test_start_ride_invalid_status_requested(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create passenger account
    passenger_info = get_account_info
    passenger_info.is_driver = False
    passenger_info.car_plate = ""
    context._is_passenger = True

    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    # Create ride request (status will be REQUESTED)
    ride_request = get_ride_request
    ride_request.passenger_id = passenger_id

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Try to start ride without accepting it first - should fail
    context._is_passenger = False  # Switch to driver context
    with pytest.raises(ValueError, match="Invalid status"):
        await app_test_client.run(
            func=start_ride,
            request=StringValue(value=ride_id),
            context=context,
        )


async def test_start_ride_nonexistent_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    context = get_mock_context
    context._is_passenger = False  # Set as driver

    # Try to start non-existent ride
    with pytest.raises(ValueError, match="Ride with id nonexistent_ride not found"):
        await app_test_client.run(
            func=start_ride,
            request=StringValue(value="nonexistent_ride"),
            context=context,
        )


async def test_start_ride_already_in_progress(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create passenger account
    passenger_info = get_account_info
    passenger_info.is_driver = False
    passenger_info.car_plate = ""
    context._is_passenger = True

    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    # Create ride request
    ride_request = get_ride_request
    ride_request.passenger_id = passenger_id

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Create driver account
    driver_info = AccountInfo(
        name="Driver User",
        email="driver@example.com",
        sin="123456782",
        car_plate="DEF-5678",
        is_driver=True,
    )
    context._is_passenger = False  # Switch to driver

    driver_resp = await app_test_client.run(
        func=signup_account,
        request=driver_info,
        context=context,
    )
    driver_id = driver_resp.value

    # Accept and start the ride
    accept_request = KeyValueStr(key=ride_id, value=driver_id)
    await app_test_client.run(
        func=accept_ride,
        request=accept_request,
        context=context,
    )

    await app_test_client.run(
        func=start_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Try to start the ride again - should fail
    with pytest.raises(ValueError, match="Invalid status"):
        await app_test_client.run(
            func=start_ride,
            request=StringValue(value=ride_id),
            context=context,
        )


async def test_start_ride_completed_status(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create passenger account
    passenger_info = get_account_info
    passenger_info.is_driver = False
    passenger_info.car_plate = ""
    context._is_passenger = True

    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    # Create ride request
    ride_request = get_ride_request
    ride_request.passenger_id = passenger_id

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Create driver account
    driver_info = AccountInfo(
        name="Driver User",
        email="driver@example.com",
        sin="123456782",
        car_plate="DEF-5678",
        is_driver=True,
    )
    context._is_passenger = False  # Switch to driver

    driver_resp = await app_test_client.run(
        func=signup_account,
        request=driver_info,
        context=context,
    )
    driver_id = driver_resp.value

    # Accept the ride and manually set status to COMPLETED
    accept_request = KeyValueStr(key=ride_id, value=driver_id)
    await app_test_client.run(
        func=accept_ride,
        request=accept_request,
        context=context,
    )

    # Manually set ride status to COMPLETED to test edge case
    ride_repo = context._mock_ride_repo
    ride = await ride_repo.get_by_ride_id(ride_id)
    ride.status = RideStatus.COMPLETED
    await ride_repo.update_ride(ride)

    # Try to start completed ride - should fail
    with pytest.raises(ValueError, match="Invalid status"):
        await app_test_client.run(
            func=start_ride,
            request=StringValue(value=ride_id),
            context=context,
        )
