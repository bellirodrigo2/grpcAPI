from datetime import datetime
from unittest.mock import patch

import pytest
from typing_extensions import Tuple

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import (
    accept_ride,
    request_ride,
    start_ride,
    update_position,
)
from example.guber.server.domain import KeyValueStr, RideStatus
from example.guber.server.domain.service.farecalc import (
    NormalFare,
    OvernightFare,
    SundayFare,
)
from example.guber.tests.fixtures import get_position_repo_test, get_ride_repo_test
from grpcAPI.protobuf import StringValue
from grpcAPI.testclient import ContextMock, TestClient

from .helpers import (
    EXPECTED_END_LAT,
    EXPECTED_END_LONG,
    create_coord,
    create_driver_info,
    create_passenger_info,
    create_position,
    create_ride_request,
    get_unique_email,
    get_unique_sin,
)


async def setup_ride_in_progress(
    app_test_client: TestClient,
    context: ContextMock,
    unique_index: int = 0,
) -> Tuple[str, str, str]:
    """Helper function to set up a ride in progress status"""
    # Create unique passenger account
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 300 + unique_index),
        sin=get_unique_sin(unique_index % 5),
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
        email=get_unique_email("driver", 300 + unique_index),
        sin=get_unique_sin((unique_index + 1) % 20),
    )

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
    get_mock_context: ContextMock,
):
    """Test position update during normal business hours (rate: 2.1/km)"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_in_progress(
        app_test_client, context, unique_index=0
    )

    # Mock fare calculator to return normal fare
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        # Set initial position
        async with get_position_repo_test() as position_repo:
            coord = create_coord(lat=-27.584905257808835, long=-48.545022195325124)
            await position_repo.create_position(
                ride_id, coord, updated_at=datetime.now()
            )

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
    async with get_ride_repo_test() as ride_repo:
        updated_ride = await ride_repo.get_by_ride_id(ride_id)
        assert updated_ride is not None
        assert updated_ride.status == RideStatus.IN_PROGRESS

    # Verify position was updated in position repo
    async with get_position_repo_test() as position_repo:
        current_pos = await position_repo.get_current_position(ride_id)
        assert current_pos.coord.lat == pytest.approx(EXPECTED_END_LAT, abs=1e-3)
        assert current_pos.coord.long == pytest.approx(EXPECTED_END_LONG, abs=1e-3)

    # Distance between the coordinates is approximately 10 km, normal rate is 2.1
    # So fare should be approximately 10 * 2.1 = 21
    expected_fare = 10 * 2.1
    assert updated_ride.fare == pytest.approx(
        expected_fare, abs=1.0
    )  # Allow small rounding differences


async def test_update_position_overnight_fare(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position update during overnight hours (rate: 3.9/km)"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_in_progress(
        app_test_client, context, unique_index=1
    )

    # Mock fare calculator to return overnight fare
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=OvernightFare(),
    ):
        # Set initial position
        async with get_position_repo_test() as position_repo:
            coord = create_coord(lat=-27.584905257808835, long=-48.545022195325124)
            await position_repo.create_position(
                ride_id, coord, updated_at=datetime.now()
            )

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
    async with get_ride_repo_test() as ride_repo:
        updated_ride = await ride_repo.get_by_ride_id(ride_id)
        expected_fare = 10 * 3.9  # 39.0
        assert updated_ride.fare == pytest.approx(expected_fare, abs=1.0)


async def test_update_position_sunday_fare(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position update during Sunday (rate: 5.0/km)"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_in_progress(
        app_test_client, context, unique_index=2
    )

    # Mock fare calculator to return Sunday fare
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=SundayFare(),
    ):
        # Set initial position
        async with get_position_repo_test() as position_repo:
            await position_repo.create_position(
                ride_id,
                create_coord(-27.584905257808835, -48.545022195325124),
                updated_at=datetime.now(),
            )

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
    async with get_ride_repo_test() as ride_repo:
        updated_ride = await ride_repo.get_by_ride_id(ride_id)
        expected_fare = 10 * 5.0  # 50.0
        assert updated_ride.fare == pytest.approx(expected_fare, abs=1.0)


async def test_update_position_invalid_status(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test that position update fails for rides not in progress"""
    context = get_mock_context

    # Create unique passenger and request ride (but don't start it)
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 17), sin=get_unique_sin(7)
    )

    passenger_resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    passenger_id = passenger_resp.value

    ride_request = create_ride_request(passenger_id=passenger_id)

    ride_resp = await app_test_client.run(
        func=request_ride,
        request=ride_request,
        context=context,
    )
    ride_id = ride_resp.value

    # Try to update position on a ride that's only REQUESTED (not IN_PROGRESS)
    new_position = create_position(ride_id, -27.496887588317275, -48.522234807851476)

    async with get_position_repo_test() as position_repo:
        await position_repo.create_position(
            ride_id,
            create_coord(-27.584905257808835, -48.545022195325124),
            updated_at=datetime.now(),
        )

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
    get_mock_context: ContextMock,
):
    """Test multiple position updates accumulate fare correctly"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_in_progress(
        app_test_client, context, unique_index=3
    )

    # Mock fare calculator to return normal fare
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        async with get_position_repo_test() as position_repo:
            # First position update
            await position_repo.create_position(
                ride_id,
                create_coord(-27.584905257808835, -48.545022195325124),
                updated_at=datetime.now(),
            )
            position1 = create_position(
                ride_id, -27.590000000000000, -48.550000000000000
            )

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
        # Verify final position
        current = await position_repo.get_current_position(ride_id)
        assert current.coord.lat == pytest.approx(-27.496887588317275, abs=1e-3)
        assert current.coord.long == pytest.approx(-48.522234807851476, abs=1e-3)

    async with get_ride_repo_test() as ride_repo:
        updated_ride = await ride_repo.get_by_ride_id(ride_id)
        assert (
            updated_ride.fare > 0
        )  # Should have accumulated fare from both position updates
