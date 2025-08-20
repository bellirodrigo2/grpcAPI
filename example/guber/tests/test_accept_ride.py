import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import accept_ride, request_ride
from example.guber.server.domain import AccountInfo, RideRequest, RideStatus
from grpcAPI.protobuf.lib.prototypes_pb2 import KeyValueStr
from grpcAPI.testclient import ContextMock, TestClient

pytest_plugins = ["example.guber.tests.fixtures"]


async def test_accept_ride(
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

    # Create driver account with different email and SIN
    driver_info = AccountInfo(
        name="Driver User",
        email="driver@example.com",
        sin="123456782",
        car_plate="DEF-5678",
        is_driver=True,
    )
    context._is_passenger = False  # Switch to driver for signup

    driver_resp = await app_test_client.run(
        func=signup_account,
        request=driver_info,
        context=context,
    )
    driver_id = driver_resp.value

    # Accept the ride
    request = KeyValueStr(key=ride_id, value=driver_id)
    await app_test_client.run(
        func=accept_ride,
        request=request,
        context=context,
    )

    # Verify ride was accepted
    ride_repo = context._mock_ride_repo
    ride = await ride_repo.get_by_ride_id(ride_id)
    assert ride is not None
    assert ride.status == RideStatus.ACCEPTED
    assert ride.driver_id == driver_id
    assert ride.accepted_at is not None


async def test_accept_ride_driver_has_active_ride(
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

    # Accept the ride first time
    request = KeyValueStr(key=ride_id, value=driver_id)
    await app_test_client.run(
        func=accept_ride,
        request=request,
        context=context,
    )

    # Now the driver should have an active ride, try to accept the same ride again - should fail
    with pytest.raises(ValueError, match="This driver has an active ride"):
        await app_test_client.run(
            func=accept_ride,
            request=request,
            context=context,
        )


async def test_accept_ride_passenger_cannot_accept(
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

    # Try to accept ride as passenger - should fail
    context._is_passenger = True  # Keep as passenger
    request = KeyValueStr(key=ride_id, value=passenger_id)
    with pytest.raises(ValueError, match="This account is not from a driver"):
        await app_test_client.run(
            func=accept_ride,
            request=request,
            context=context,
        )


async def test_accept_ride_nonexistent_ride(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create driver account
    driver_info = get_account_info
    driver_info.is_driver = True
    context._is_passenger = False

    driver_resp = await app_test_client.run(
        func=signup_account,
        request=driver_info,
        context=context,
    )
    driver_id = driver_resp.value

    # Try to accept non-existent ride
    request = KeyValueStr(key="nonexistent_ride", value=driver_id)
    with pytest.raises(ValueError, match="Ride not found: Id: nonexistent_ride"):
        await app_test_client.run(
            func=accept_ride,
            request=request,
            context=context,
        )
