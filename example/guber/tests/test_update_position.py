from unittest.mock import patch

import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import (
    accept_ride,
    request_ride,
    start_ride,
    update_position,
)
from example.guber.server.domain import AccountInfo, Position, RideRequest, RideStatus
from example.guber.server.domain.service.farecalc import (
    NormalFare,
    OvernightFare,
    SundayFare,
)
from example.guber.tests.mocks import get_mock_position_repo
from grpcAPI.protobuf import StringValue
from grpcAPI.protobuf.lib.prototypes_pb2 import KeyValueStr
from grpcAPI.testclient import ContextMock, TestClient

pytest_plugins = ["example.guber.tests.fixtures"]


def create_position(ride_id: str, lat: float, long: float) -> Position:
    """Helper function to create Position objects"""
    position = Position()
    position.ride_id = ride_id
    position.lat = lat
    position.long = long
    # Set current timestamp
    position.updated_at.GetCurrentTime()
    return position


async def setup_ride_in_progress(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    context: ContextMock,
) -> tuple[str, str, str]:
    """Helper function to set up a ride in progress status"""
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

    return ride_id, passenger_id, driver_id


async def test_update_position_normal_fare(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test position update during normal business hours (rate: 2.1/km)"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_in_progress(
        app_test_client, get_account_info, get_ride_request, context
    )

    # Mock the accepted_at timestamp to be during business hours (10:00 AM on a Wednesday)
    ride_repo = context._mock_ride_repo

    # Mock fare calculator to return normal fare
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        # Set initial position
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Update to new position
        new_position = create_position(
            ride_id, -27.496887588317275, -48.522234807851476
        )

        await app_test_client.run(
            func=update_position,
            request=new_position,
            context=context,
        )

    # Verify position was updated and fare calculated
    updated_ride = await ride_repo.get_by_ride_id(ride_id)
    assert updated_ride is not None
    assert updated_ride.status == RideStatus.IN_PROGRESS

    # Verify position was updated in position repo
    position_repo = get_mock_position_repo(context)
    current_lat, current_long = await position_repo.get_current_position(ride_id)
    assert abs(current_lat - (-27.496887588317275)) < 0.0001
    assert abs(current_long - (-48.522234807851476)) < 0.0001

    # Distance between the coordinates is approximately 10 km, normal rate is 2.1
    # So fare should be approximately 10 * 2.1 = 21
    expected_fare = 10 * 2.1
    assert (
        abs(updated_ride.fare - expected_fare) < 1.0
    )  # Allow small rounding differences


async def test_update_position_overnight_fare(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test position update during overnight hours (rate: 3.9/km)"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_in_progress(
        app_test_client, get_account_info, get_ride_request, context
    )

    ride_repo = context._mock_ride_repo

    # Mock fare calculator to return overnight fare
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=OvernightFare(),
    ):
        # Set initial position
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Update to new position
        new_position = create_position(
            ride_id, -27.496887588317275, -48.522234807851476
        )

        await app_test_client.run(
            func=update_position,
            request=new_position,
            context=context,
        )

    # Verify fare calculated with overnight rate
    updated_ride = await ride_repo.get_by_ride_id(ride_id)
    expected_fare = 10 * 3.9  # 39.0
    assert abs(updated_ride.fare - expected_fare) < 1.0


async def test_update_position_sunday_fare(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test position update during Sunday (rate: 5.0/km)"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_in_progress(
        app_test_client, get_account_info, get_ride_request, context
    )

    ride_repo = context._mock_ride_repo

    # Mock fare calculator to return Sunday fare
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=SundayFare(),
    ):
        # Set initial position
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Update to new position
        new_position = create_position(
            ride_id, -27.496887588317275, -48.522234807851476
        )

        await app_test_client.run(
            func=update_position,
            request=new_position,
            context=context,
        )

    # Verify fare calculated with Sunday rate
    updated_ride = await ride_repo.get_by_ride_id(ride_id)
    expected_fare = 10 * 5.0  # 50.0
    assert abs(updated_ride.fare - expected_fare) < 1.0


async def test_update_position_invalid_status(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that position update fails for rides not in progress"""
    context = get_mock_context

    # Create passenger and request ride (but don't start it)
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

    ride_request = get_ride_request
    ride_request.passenger_id = passenger_id

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Try to update position on a ride that's only REQUESTED (not IN_PROGRESS)
    new_position = create_position(ride_id, -27.496887588317275, -48.522234807851476)

    context._is_passenger = False  # Switch to driver context
    with pytest.raises(ValueError, match="Invalid status"):
        await app_test_client.run(
            func=update_position,
            request=new_position,
            context=context,
        )


async def test_update_position_nonexistent_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position update for non-existent ride"""
    context = get_mock_context
    context._is_passenger = False  # Set as driver

    # Try to update position for non-existent ride
    new_position = create_position(
        "nonexistent_ride", -27.496887588317275, -48.522234807851476
    )

    with pytest.raises(ValueError, match="Ride with id nonexistent_ride not found"):
        await app_test_client.run(
            func=update_position,
            request=new_position,
            context=context,
        )


async def test_update_position_multiple_updates(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test multiple position updates accumulate fare correctly"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_in_progress(
        app_test_client, get_account_info, get_ride_request, context
    )

    ride_repo = context._mock_ride_repo

    # Mock fare calculator to return normal fare
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)

        # First position update
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)
        position1 = create_position(ride_id, -27.590000000000000, -48.550000000000000)

        await app_test_client.run(
            func=update_position,
            request=position1,
            context=context,
        )

        # Second position update
        position2 = create_position(ride_id, -27.496887588317275, -48.522234807851476)

        await app_test_client.run(
            func=update_position,
            request=position2,
            context=context,
        )

    # Verify fare accumulated from both updates
    updated_ride = await ride_repo.get_by_ride_id(ride_id)
    assert (
        updated_ride.fare > 0
    )  # Should have accumulated fare from both position updates

    # Verify final position
    current_lat, current_long = await position_repo.get_current_position(ride_id)
    assert abs(current_lat - (-27.496887588317275)) < 0.0001
    assert abs(current_long - (-48.522234807851476)) < 0.0001
