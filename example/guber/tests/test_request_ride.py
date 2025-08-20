import pytest

from example.guber.server.application.usecase.ride import request_ride
from example.guber.server.domain import RideRequest
from grpcAPI.testclient import ContextMock, TestClient

pytest_plugins = ["example.guber.tests.fixtures"]


async def test_request_ride(
    app_test_client: TestClient,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    context = get_mock_context
    context._is_passenger = True  # Set as passenger

    resp = await app_test_client.run(
        func=request_ride,
        request=get_ride_request,
        context=context,
    )

    assert resp.value == "ride_1"
    ride_repo = context._mock_ride_repo
    assert ride_repo.calls[0] == ("has_active_ride", "test_passenger_id")
    assert ride_repo.calls[1] == ("create_ride", get_ride_request)

    # Verify ride was created correctly
    ride = await ride_repo.get_by_ride_id("ride_1")
    assert ride is not None
    assert ride.ride_request.passenger_id == "test_passenger_id"
    assert ride.ride_request.from_lat == -27.584905257808835
    assert ride.ride_request.from_long == -48.545022195325124
    assert ride.ride_request.to_lat == -27.496887588317275
    assert ride.ride_request.to_long == -48.522234807851476


async def test_request_ride_not_passenger(
    app_test_client: TestClient,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    context = get_mock_context
    context._is_passenger = False  # Set as driver, not passenger

    with pytest.raises(ValueError, match="This account is not from a passenger"):
        await app_test_client.run(
            func=request_ride,
            request=get_ride_request,
            context=context,
        )


async def test_request_ride_has_active_ride(
    app_test_client: TestClient,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    context = get_mock_context
    context._is_passenger = True

    # First request should succeed
    await app_test_client.run(
        func=request_ride,
        request=get_ride_request,
        context=context,
    )

    # Second request should fail due to active ride
    with pytest.raises(ValueError, match="This passenger has an active ride"):
        await app_test_client.run(
            func=request_ride,
            request=get_ride_request,
            context=context,
        )


async def test_request_ride_different_coordinates(
    app_test_client: TestClient,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    different_ride_request = get_ride_request
    different_ride_request.from_lat = -23.550520  # São Paulo coordinates
    different_ride_request.from_long = -46.633309
    different_ride_request.to_lat = -23.561414
    different_ride_request.to_long = -46.656166

    context = get_mock_context
    context._is_passenger = True

    resp = await app_test_client.run(
        func=request_ride,
        request=different_ride_request,
        context=context,
    )

    assert resp.value == "ride_1"
    ride_repo = context._mock_ride_repo
    ride = await ride_repo.get_by_ride_id("ride_1")
    assert ride is not None
    assert ride.ride_request.from_lat == -23.550520
    assert ride.ride_request.from_long == -46.633309
    assert ride.ride_request.to_lat == -23.561414
    assert ride.ride_request.to_long == -46.656166
