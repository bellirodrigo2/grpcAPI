from unittest.mock import patch

import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import (
    accept_ride,
    finish_ride,
    get_ride,
    request_ride,
    start_ride,
    update_position,
)
from example.guber.server.domain import RideSnapshot, RideStatus
from example.guber.server.domain.service.farecalc import NormalFare
from example.guber.tests.mocks import get_mock_position_repo
from grpcAPI.protobuf import KeyValueStr, StringValue
from grpcAPI.testclient import ContextMock, TestClient

from .helpers import (
    create_driver_info,
    create_passenger_info,
    create_position,
    create_ride_request,
    get_unique_email,
    get_unique_sin,
)



async def setup_complete_ride_workflow(
    app_test_client: TestClient,
    context: ContextMock,
    unique_index: int = 0,
    status: RideStatus = RideStatus.COMPLETED,
) -> tuple[str, str, str]:
    """Helper function to set up rides at different stages of completion"""
    # Create unique passenger account
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 400 + unique_index),
        sin=get_unique_sin(unique_index % 20),
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

    if status == RideStatus.REQUESTED:
        return ride_id, passenger_id, ""

    # Create unique driver account
    driver_info = create_driver_info(
        email=get_unique_email("driver", 400 + unique_index),
        sin=get_unique_sin((unique_index + 1) % 20),
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

    if status == RideStatus.ACCEPTED:
        return ride_id, passenger_id, driver_id

    # Start the ride
    await app_test_client.run(
        func=start_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    if status == RideStatus.IN_PROGRESS:
        # Add position updates
        with patch(
            "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
            return_value=NormalFare(),
        ):
            position_repo = get_mock_position_repo(context)
            position_repo.set_position(
                ride_id, -27.584905257808835, -48.545022195325124
            )

            new_position = create_position(
                ride_id, -27.496887588317275, -48.522234807851476
            )
            await app_test_client.run(
                func=update_position,
                request=new_position,
                context=context,
            )
        return ride_id, passenger_id, driver_id

    # Complete the ride (add position first)
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        new_position = create_position(
            ride_id, -27.496887588317275, -48.522234807851476
        )
        await app_test_client.run(
            func=update_position,
            request=new_position,
            context=context,
        )

    # Finish the ride
    await app_test_client.run(
        func=finish_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    return ride_id, passenger_id, driver_id


async def test_get_ride_requested_status(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test getting ride information for a REQUESTED ride"""
    context = get_mock_context

    ride_id, passenger_id, _ = await setup_complete_ride_workflow(
        app_test_client,
        context,
        unique_index=0,
        status=RideStatus.REQUESTED,
    )

    # Get ride information
    ride_info_resp = await app_test_client.run(
        func=get_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    ride_info = ride_info_resp
    assert isinstance(ride_info, RideSnapshot)
    assert ride_info.ride.ride_id == ride_id
    assert ride_info.ride.status == RideStatus.REQUESTED
    assert ride_info.ride.driver_id == ""  # No driver assigned yet
    assert ride_info.ride.fare == 0.0  # No fare accumulated
    assert not ride_info.ride.HasField("accepted_at")  # Not accepted yet
    assert not ride_info.ride.HasField("finished_at")  # Not finished
    assert ride_info.current_location.coord.lat == 0.0  # Default position from mock
    assert ride_info.current_location.coord.long == 0.0


async def test_get_ride_accepted_status(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test getting ride information for an ACCEPTED ride"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_complete_ride_workflow(
        app_test_client,
        context,
        unique_index=1,
        status=RideStatus.ACCEPTED,
    )

    # Get ride information
    ride_info_resp = await app_test_client.run(
        func=get_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    ride_info = ride_info_resp
    assert ride_info.ride.ride_id == ride_id
    assert ride_info.ride.status == RideStatus.ACCEPTED
    assert ride_info.ride.driver_id == driver_id
    assert ride_info.ride.fare == 0.0  # No fare accumulated yet
    assert ride_info.ride.HasField("accepted_at")  # Has accepted timestamp
    assert not ride_info.ride.HasField("finished_at")  # Not finished
    assert ride_info.current_location.coord.lat == 0.0  # No position updates yet
    assert ride_info.current_location.coord.long == 0.0


async def test_get_ride_in_progress_status(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test getting ride information for an IN_PROGRESS ride with position updates"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_complete_ride_workflow(
        app_test_client,
        context,
        unique_index=2,
        status=RideStatus.IN_PROGRESS,
    )

    # Get ride information
    ride_info_resp = await app_test_client.run(
        func=get_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    ride_info = ride_info_resp
    assert ride_info.ride.ride_id == ride_id
    assert ride_info.ride.status == RideStatus.IN_PROGRESS
    assert ride_info.ride.driver_id == driver_id
    assert (
        ride_info.ride.fare > 0.0
    )  # Should have accumulated fare from position update
    assert ride_info.ride.HasField("accepted_at")  # Has accepted timestamp
    assert not ride_info.ride.HasField("finished_at")  # Not finished yet
    # Should have updated position from position update
    assert abs(ride_info.current_location.coord.lat - (-27.496887588317275)) < 0.0001
    assert abs(ride_info.current_location.coord.long - (-48.522234807851476)) < 0.0001


async def test_get_ride_completed_status(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test getting ride information for a COMPLETED ride"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_complete_ride_workflow(
        app_test_client,
        context,
        unique_index=3,
        status=RideStatus.COMPLETED,
    )

    # Get ride information
    ride_info_resp = await app_test_client.run(
        func=get_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    ride_info = ride_info_resp
    assert ride_info.ride.ride_id == ride_id
    assert ride_info.ride.status == RideStatus.COMPLETED
    assert ride_info.ride.driver_id == driver_id
    assert ride_info.ride.fare > 0.0  # Should have accumulated fare
    assert ride_info.ride.HasField("accepted_at")  # Has accepted timestamp
    assert ride_info.ride.HasField("finished_at")  # Has finished timestamp
    # Should have final position
    assert abs(ride_info.current_location.coord.lat - (-27.496887588317275)) < 0.0001
    assert abs(ride_info.current_location.coord.long - (-48.522234807851476)) < 0.0001


async def test_get_ride_nonexistent_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test get_ride for non-existent ride"""
    context = get_mock_context

    # Try to get non-existent ride
    with pytest.raises(ValueError, match="Ride with id nonexistent_ride not found"):
        await app_test_client.run(
            func=get_ride,
            request=StringValue(value="nonexistent_ride"),
            context=context,
        )


async def test_get_ride_with_multiple_position_updates(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test get_ride returns latest position after multiple updates"""
    context = get_mock_context

    # Set up ride in progress
    ride_id, passenger_id, driver_id = await setup_complete_ride_workflow(
        app_test_client,
        context,
        unique_index=2,
        status=RideStatus.IN_PROGRESS,
    )

    # Add another position update
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):

        # Update to a new position
        newer_position = create_position(
            ride_id, -27.600000000000000, -48.600000000000000
        )
        await app_test_client.run(
            func=update_position,
            request=newer_position,
            context=context,
        )

    # Get ride information - should have latest position
    ride_info_resp = await app_test_client.run(
        func=get_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    ride_info = ride_info_resp
    # Should reflect the latest position update
    assert abs(ride_info.current_location.coord.lat - (-27.600000000000000)) < 0.0001
    assert abs(ride_info.current_location.coord.long - (-48.600000000000000)) < 0.0001
    # Should have accumulated more fare from multiple position updates
    assert ride_info.ride.fare > 21.0  # More than single position update fare


async def test_get_ride_ride_info_structure(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test that get_ride returns properly structured RideInfo object"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_complete_ride_workflow(
        app_test_client,
        context,
        unique_index=2,
        status=RideStatus.IN_PROGRESS,
    )

    # Get ride information
    ride_info_resp = await app_test_client.run(
        func=get_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    ride_info = ride_info_resp

    # Verify RideSnapshot structure
    assert hasattr(ride_info, "ride")
    assert hasattr(ride_info, "current_location")
    assert hasattr(ride_info.current_location, "coord")

    # Verify nested ride structure
    assert hasattr(ride_info.ride, "ride_id")
    assert hasattr(ride_info.ride, "passenger_id")
    assert hasattr(ride_info.ride, "driver_id")
    assert hasattr(ride_info.ride, "status")
    assert hasattr(ride_info.ride, "fare")
    assert hasattr(ride_info.ride, "start_point")
    assert hasattr(ride_info.ride, "end_point")

    # Verify coordinate structure
    assert hasattr(ride_info.ride.start_point, "lat")
    assert hasattr(ride_info.ride.start_point, "long")
    assert hasattr(ride_info.ride.end_point, "lat")
    assert hasattr(ride_info.ride.end_point, "long")

    # Verify actual values match expectations (flattened structure)
    assert ride_info.ride.passenger_id == passenger_id
    assert ride_info.ride.start_point.lat == -27.584905257808835
    assert ride_info.ride.start_point.long == -48.545022195325124
    assert ride_info.ride.end_point.lat == -27.496887588317275
    assert ride_info.ride.end_point.long == -48.522234807851476


async def test_get_ride_no_position_updates(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test get_ride for ride with no position updates (returns default position)"""
    context = get_mock_context

    # Create and start a ride but don't update position
    ride_id, passenger_id, driver_id = await setup_complete_ride_workflow(
        app_test_client,
        context,
        unique_index=1,
        status=RideStatus.ACCEPTED,
    )

    # Start the ride but don't update position
    await app_test_client.run(
        func=start_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Get ride information
    ride_info_resp = await app_test_client.run(
        func=get_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    ride_info = ride_info_resp
    assert ride_info.ride.status == RideStatus.IN_PROGRESS
    assert ride_info.ride.fare == 0.0  # No position updates, no fare
    # Should return initial position at ride start point
    assert ride_info.current_location.coord.lat == -27.584905257808835
    assert ride_info.current_location.coord.long == -48.545022195325124
