import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import request_ride
from example.guber.tests.fixtures import get_ride_repo_test
from grpcAPI.testclient import ContextMock, TestClient

from .helpers import (
    SAO_PAULO_END,
    SAO_PAULO_START,
    create_driver_info,
    create_passenger_info,
    create_ride_request,
    get_unique_email,
    get_unique_sin,
)


async def test_request_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create unique passenger and ride request
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 1), sin=get_unique_sin(1)
    )
    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    ride_request = create_ride_request(passenger_id=passenger_id)

    resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )

    assert resp.value.startswith("test_ride_id")
    rideid = resp.value
    async with get_ride_repo_test() as ride_repo:
        ride = await ride_repo.get_by_ride_id(rideid)
        assert ride is not None
        assert ride.passenger_id == passenger_id
        assert ride.start_point.lat == -27.584905257808835
        assert ride.start_point.long == -48.545022195325124
        assert ride.end_point.lat == -27.496887588317275
        assert ride.end_point.long == -48.522234807851476


async def test_request_ride_not_passenger(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    # Create a driver account for this test
    from example.guber.server.application.usecase.account import signup_account

    context = get_mock_context
    context._is_passenger = False  # Set as driver context for signup

    # Create unique driver info
    driver_info = create_driver_info(
        email=get_unique_email("driver", 2), sin=get_unique_sin(2)
    )

    driver_resp = await app_test_client.run(
        func=signup_account,
        request=driver_info,
        context=context,
    )
    driver_id = driver_resp.value

    # Create ride request using driver ID (should fail)
    driver_ride_request = create_ride_request(
        passenger_id=driver_id, start_point=SAO_PAULO_START, end_point=SAO_PAULO_END
    )

    with pytest.raises(ValueError, match="This account is not from a passenger"):
        await app_test_client.run(
            func=request_ride,
            request=driver_ride_request,
            context=context,
        )


async def test_request_ride_has_active_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    from example.guber.server.application.usecase.account import signup_account

    context = get_mock_context
    context._is_passenger = True

    # Create unique passenger
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 3), sin=get_unique_sin(3)
    )
    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    ride_request = create_ride_request(passenger_id=passenger_id)

    # First request should succeed
    await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )

    # Second request should fail due to active ride
    with pytest.raises(ValueError, match="This passenger has an active ride"):
        await app_test_client.run(
            func=request_ride,
            request=ride_request,
            context=context,
        )


async def test_request_ride_different_coordinates(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    from example.guber.server.application.usecase.account import signup_account

    context = get_mock_context
    context._is_passenger = True

    # Create unique passenger
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 4), sin=get_unique_sin(4)
    )
    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    # Create ride request with São Paulo coordinates
    different_ride_request = create_ride_request(
        passenger_id=passenger_id, start_point=SAO_PAULO_START, end_point=SAO_PAULO_END
    )

    resp = await app_test_client.run(
        func=request_ride,
        request=different_ride_request,
        context=context,
    )

    assert resp.value.startswith("test_ride_id")
    rideid = resp.value
    async with get_ride_repo_test() as ride_repo:
        ride = await ride_repo.get_by_ride_id(rideid)
        assert ride is not None
        assert ride.start_point.lat == -23.550520
        assert ride.start_point.long == -46.633309
        assert ride.end_point.lat == -23.561414
        assert ride.end_point.long == -46.656166
