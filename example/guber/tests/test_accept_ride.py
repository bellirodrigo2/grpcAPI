import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import accept_ride, request_ride
from example.guber.server.domain import KeyValueStr, RideStatus
from grpcAPI.testclient import ContextMock, TestClient

from .fixtures import get_ride_repo_test
from .helpers import (
    create_driver_info,
    create_passenger_info,
    create_ride_request,
    get_unique_email,
    get_unique_sin,
)


async def test_accept_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create unique passenger account
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 5), sin=get_unique_sin(0)
    )

    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    # Create ride request
    ride_request = create_ride_request(passenger_id=passenger_id)

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Create unique driver account
    driver_info = create_driver_info(
        email=get_unique_email("driver", 5), sin=get_unique_sin(1)
    )

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
    async with get_ride_repo_test() as ride_repo:
        ride = await ride_repo.get_by_ride_id(ride_id)
        assert ride is not None
        assert ride.status == RideStatus.ACCEPTED
        assert ride.driver_id == driver_id
        assert ride.accepted_at is not None


async def test_accept_ride_driver_has_active_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create unique passenger account
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 6), sin=get_unique_sin(2)
    )

    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    # Create ride request
    ride_request = create_ride_request(passenger_id=passenger_id)

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Create unique driver account
    driver_info = create_driver_info(
        email=get_unique_email("driver", 6), sin=get_unique_sin(3)
    )

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

    with pytest.raises(ValueError, match="This driver has an active ride"):
        await app_test_client.run(
            func=accept_ride,
            request=request,
            context=context,
        )


async def test_accept_ride_passenger_cannot_accept(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create unique passenger account
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 7), sin=get_unique_sin(4)
    )

    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    # Create ride request
    ride_request = create_ride_request(passenger_id=passenger_id)

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Try to accept ride as passenger - should fail
    request = KeyValueStr(key=ride_id, value=passenger_id)
    with pytest.raises(ValueError, match="This account is not from a driver"):
        await app_test_client.run(
            func=accept_ride,
            request=request,
            context=context,
        )


async def test_accept_ride_nonexistent_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create unique driver account
    driver_info = create_driver_info(
        email=get_unique_email("driver", 7), sin=get_unique_sin(0)
    )

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
