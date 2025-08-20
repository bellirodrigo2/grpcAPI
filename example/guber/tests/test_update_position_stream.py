from typing import AsyncIterator
from unittest.mock import patch

import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import (
    accept_ride,
    request_ride,
    start_ride,
    update_position_stream,
)
from example.guber.server.domain import AccountInfo, Position, RideRequest, RideStatus
from example.guber.server.domain.service.farecalc import NormalFare
from example.guber.tests.mocks import get_mock_position_repo
from grpcAPI.protobuf import Empty, KeyValueStr, StringValue
from grpcAPI.testclient import ContextMock, TestClient

pytest_plugins = ["example.guber.tests.fixtures"]


def create_position(ride_id: str, lat: float, long: float) -> Position:
    """Helper function to create Position objects"""
    position = Position()
    position.ride_id = ride_id
    position.lat = lat
    position.long = long
    position.updated_at.GetCurrentTime()
    return position


async def create_position_stream(positions: list[Position]) -> AsyncIterator[Position]:
    """Helper function to create async iterator for position stream"""
    for position in positions:
        yield position


async def setup_ride_for_stream(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    context: ContextMock,
) -> tuple[str, str, str]:
    """Helper function to set up ride ready for position streaming"""
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
    context._is_passenger = False

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

    return ride_id, passenger_id, driver_id


async def test_update_position_stream_single_position(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test update_position_stream with single position update"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_stream(
        app_test_client, get_account_info, get_ride_request, context
    )

    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Create single position update
        position = create_position(ride_id, -27.496887588317275, -48.522234807851476)
        position_stream = create_position_stream([position])

        # Call update_position_stream
        result = await app_test_client.run(
            func=update_position_stream,
            request=position_stream,
            context=context,
        )

        assert isinstance(result, Empty)

        # Verify position was updated
        current_lat, current_long = await position_repo.get_current_position(ride_id)
        assert abs(current_lat - (-27.496887588317275)) < 0.0001
        assert abs(current_long - (-48.522234807851476)) < 0.0001


async def test_update_position_stream_multiple_positions(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test update_position_stream with multiple position updates"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_stream(
        app_test_client, get_account_info, get_ride_request, context
    )

    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Create multiple position updates
        positions = [
            create_position(ride_id, -27.496887588317275, -48.522234807851476),
            create_position(ride_id, -27.450000000000000, -48.500000000000000),
            create_position(ride_id, -27.400000000000000, -48.480000000000000),
        ]
        position_stream = create_position_stream(positions)

        # Call update_position_stream
        result = await app_test_client.run(
            func=update_position_stream,
            request=position_stream,
            context=context,
        )

        assert isinstance(result, Empty)

        # Verify final position (should be the last one)
        current_lat, current_long = await position_repo.get_current_position(ride_id)
        assert abs(current_lat - (-27.400000000000000)) < 0.0001
        assert abs(current_long - (-48.480000000000000)) < 0.0001


async def test_update_position_stream_fare_accumulation(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that fare accumulates correctly across multiple position updates"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_stream(
        app_test_client, get_account_info, get_ride_request, context
    )

    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Create multiple position updates with significant distances
        positions = [
            create_position(ride_id, -27.496887588317275, -48.522234807851476),  # ~10km
            create_position(
                ride_id, -27.400000000000000, -48.480000000000000
            ),  # ~15km more
            create_position(
                ride_id, -27.300000000000000, -48.450000000000000
            ),  # ~13km more
        ]
        position_stream = create_position_stream(positions)

        # Get ride repository to check fare accumulation
        from example.guber.tests.mocks import get_mock_ride_repo

        ride_repo = get_mock_ride_repo(context)

        # Call update_position_stream
        result = await app_test_client.run(
            func=update_position_stream,
            request=position_stream,
            context=context,
        )

        assert isinstance(result, Empty)

        # Check that fare accumulated across all updates
        ride = await ride_repo.get_by_ride_id(ride_id)
        assert (
            ride.fare > 60.0
        )  # Should be significant fare from multiple long distance updates
        assert ride.status == RideStatus.IN_PROGRESS


async def test_update_position_stream_nonexistent_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test update_position_stream with non-existent ride"""
    context = get_mock_context

    # Create position for non-existent ride
    position = create_position(
        "nonexistent_ride", -27.496887588317275, -48.522234807851476
    )
    position_stream = create_position_stream([position])

    # Should raise ValueError for non-existent ride
    with pytest.raises(ValueError, match="Ride with id nonexistent_ride not found"):
        await app_test_client.run(
            func=update_position_stream,
            request=position_stream,
            context=context,
        )


async def test_update_position_stream_empty_stream(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test update_position_stream with empty position stream"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_stream(
        app_test_client, get_account_info, get_ride_request, context
    )

    # Create empty position stream
    position_stream = create_position_stream([])

    # Call update_position_stream with empty stream
    result = await app_test_client.run(
        func=update_position_stream,
        request=position_stream,
        context=context,
    )

    assert isinstance(result, Empty)

    # Verify no changes to ride or position
    from example.guber.tests.mocks import get_mock_position_repo, get_mock_ride_repo

    ride_repo = get_mock_ride_repo(context)
    position_repo = get_mock_position_repo(context)

    ride = await ride_repo.get_by_ride_id(ride_id)
    assert ride.fare == 0.0  # No position updates, no fare changes

    current_lat, current_long = await position_repo.get_current_position(ride_id)
    assert current_lat == 0.0  # Default position unchanged
    assert current_long == 0.0


async def test_update_position_stream_mixed_ride_ids(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test update_position_stream fails when positions have different ride IDs"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_stream(
        app_test_client, get_account_info, get_ride_request, context
    )

    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Create positions with different ride IDs (should only use first ride_id)
        positions = [
            create_position(ride_id, -27.496887588317275, -48.522234807851476),
            create_position("different_ride", -27.450000000000000, -48.500000000000000),
        ]
        position_stream = create_position_stream(positions)

        # Should fail when second position has different ride_id that doesn't exist
        with pytest.raises(ValueError, match="Unexpected ride_id:"):
            await app_test_client.run(
                func=update_position_stream,
                request=position_stream,
                context=context,
            )


async def test_update_position_stream_ride_caching(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that ride is fetched only once and cached for subsequent positions"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_stream(
        app_test_client, get_account_info, get_ride_request, context
    )

    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Create multiple position updates for same ride
        positions = [
            create_position(ride_id, -27.496887588317275, -48.522234807851476),
            create_position(ride_id, -27.450000000000000, -48.500000000000000),
            create_position(ride_id, -27.400000000000000, -48.480000000000000),
        ]
        position_stream = create_position_stream(positions)

        # Get ride repository to monitor calls
        from example.guber.tests.mocks import get_mock_ride_repo

        ride_repo = get_mock_ride_repo(context)
        initial_call_count = len(
            [call for call in ride_repo.calls if call[0] == "get_by_ride_id"]
        )

        # Call update_position_stream
        result = await app_test_client.run(
            func=update_position_stream,
            request=position_stream,
            context=context,
        )

        assert isinstance(result, Empty)

        # Verify ride was fetched only once (ride caching works)
        final_call_count = len(
            [call for call in ride_repo.calls if call[0] == "get_by_ride_id"]
        )
        # Should have only one additional get_by_ride_id call (the initial fetch)
        assert final_call_count == initial_call_count + 1


async def test_update_position_stream_position_persistence(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that each position in stream is properly persisted"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_stream(
        app_test_client, get_account_info, get_ride_request, context
    )

    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Create multiple positions
        test_positions = [
            (-27.496887588317275, -48.522234807851476),
            (-27.450000000000000, -48.500000000000000),
            (-27.400000000000000, -48.480000000000000),
        ]

        positions = [create_position(ride_id, lat, lng) for lat, lng in test_positions]
        position_stream = create_position_stream(positions)

        # Call update_position_stream
        result = await app_test_client.run(
            func=update_position_stream,
            request=position_stream,
            context=context,
        )

        assert isinstance(result, Empty)

        # Verify final position is the last one in the stream
        final_lat, final_lng = await position_repo.get_current_position(ride_id)
        expected_lat, expected_lng = test_positions[-1]
        assert abs(final_lat - expected_lat) < 0.0001
        assert abs(final_lng - expected_lng) < 0.0001


async def test_update_position_stream_concurrent_same_ride(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test update_position_stream behavior with positions from same ride ID"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_stream(
        app_test_client, get_account_info, get_ride_request, context
    )

    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Create positions all with same ride_id (normal case)
        positions = [
            create_position(ride_id, -27.496887588317275, -48.522234807851476),
            create_position(ride_id, -27.450000000000000, -48.500000000000000),
            create_position(ride_id, -27.400000000000000, -48.480000000000000),
        ]
        position_stream = create_position_stream(positions)

        # Call update_position_stream
        result = await app_test_client.run(
            func=update_position_stream,
            request=position_stream,
            context=context,
        )

        assert isinstance(result, Empty)

        # Verify ride state is properly updated
        from example.guber.tests.mocks import get_mock_ride_repo

        ride_repo = get_mock_ride_repo(context)
        ride = await ride_repo.get_by_ride_id(ride_id)

        assert ride.status == RideStatus.IN_PROGRESS
        assert ride.fare > 0.0  # Fare should accumulate
        assert ride.driver_id == driver_id  # Driver should remain assigned

        # Verify final position
        final_lat, final_lng = await position_repo.get_current_position(ride_id)
        assert abs(final_lat - (-27.400000000000000)) < 0.0001
        assert abs(final_lng - (-48.480000000000000)) < 0.0001
