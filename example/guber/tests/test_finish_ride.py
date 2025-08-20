from unittest.mock import patch

import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import (
    accept_ride,
    finish_ride,
    request_ride,
    start_ride,
    update_position,
)
from example.guber.server.domain import AccountInfo, Position, RideRequest, RideStatus
from example.guber.server.domain.service.farecalc import NormalFare
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
    position.updated_at.GetCurrentTime()
    return position


async def setup_ride_with_fare(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    context: ContextMock,
) -> tuple[str, str, str]:
    """Helper function to set up a ride with accumulated fare"""
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

    # Add some fare through position updates
    with patch(
        "example.guber.server.domain.entity.ride_rules.create_fare_calculator",
        return_value=NormalFare(),
    ):
        # Set initial position
        position_repo = get_mock_position_repo(context)
        position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

        # Update position to accumulate fare
        new_position = create_position(
            ride_id, -27.496887588317275, -48.522234807851476
        )
        await app_test_client.run(
            func=update_position,
            request=new_position,
            context=context,
        )

    return ride_id, passenger_id, driver_id


async def test_finish_ride(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test successfully finishing a ride"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_with_fare(
        app_test_client, get_account_info, get_ride_request, context
    )

    # Verify ride is in progress before finishing
    ride_repo = context._mock_ride_repo
    ride = await ride_repo.get_by_ride_id(ride_id)
    assert ride.status == RideStatus.IN_PROGRESS
    assert ride.fare > 0  # Should have accumulated fare from position update
    original_fare = ride.fare

    # Verify driver has active ride before finishing
    assert ride_repo.active_rides.get(driver_id) == ride_id

    # Finish the ride
    await app_test_client.run(
        func=finish_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Verify ride was finished successfully
    finished_ride = await ride_repo.get_by_ride_id(ride_id)
    assert finished_ride is not None
    assert finished_ride.status == RideStatus.COMPLETED
    assert finished_ride.fare == original_fare  # Fare should remain the same
    assert finished_ride.HasField("finished_at")  # Should have finished timestamp
    assert finished_ride.HasField("accepted_at")  # Should still have accepted timestamp

    # Verify driver is no longer in active rides
    assert driver_id not in ride_repo.active_rides

    # Verify payment was processed (MockPaymentGateway should have been called)
    # In a real test, we could mock and verify the payment gateway was called with correct parameters


async def test_finish_ride_invalid_status_requested(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that finish_ride fails for rides not in progress - REQUESTED status"""
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

    # Try to finish ride that's only REQUESTED (not IN_PROGRESS)
    context._is_passenger = False  # Switch to driver context
    with pytest.raises(ValueError, match="Invalid status"):
        await app_test_client.run(
            func=finish_ride,
            request=StringValue(value=ride_id),
            context=context,
        )


async def test_finish_ride_invalid_status_accepted(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that finish_ride fails for rides not in progress - ACCEPTED status"""
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

    # Create driver account and accept the ride (but don't start it)
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

    # Accept the ride but don't start it
    accept_request = KeyValueStr(key=ride_id, value=driver_id)
    await app_test_client.run(
        func=accept_ride,
        request=accept_request,
        context=context,
    )

    # Try to finish ride that's only ACCEPTED (not IN_PROGRESS)
    with pytest.raises(ValueError, match="Invalid status"):
        await app_test_client.run(
            func=finish_ride,
            request=StringValue(value=ride_id),
            context=context,
        )


async def test_finish_ride_nonexistent_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test finish_ride for non-existent ride"""
    context = get_mock_context
    context._is_passenger = False  # Set as driver

    # Try to finish non-existent ride
    with pytest.raises(ValueError, match="Ride with id nonexistent_ride not found"):
        await app_test_client.run(
            func=finish_ride,
            request=StringValue(value="nonexistent_ride"),
            context=context,
        )


async def test_finish_ride_already_completed(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that finish_ride fails for already completed rides"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_with_fare(
        app_test_client, get_account_info, get_ride_request, context
    )

    # Finish the ride first time
    await app_test_client.run(
        func=finish_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Try to finish the already completed ride - should fail
    with pytest.raises(ValueError, match="Invalid status"):
        await app_test_client.run(
            func=finish_ride,
            request=StringValue(value=ride_id),
            context=context,
        )


async def test_finish_ride_with_zero_fare(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test finishing a ride with zero fare (no position updates)"""
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

    # Accept and start the ride (but don't update position)
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

    # Verify ride has zero fare before finishing
    ride_repo = context._mock_ride_repo
    ride = await ride_repo.get_by_ride_id(ride_id)
    assert ride.fare == 0.0

    # Finish the ride with zero fare
    await app_test_client.run(
        func=finish_ride,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Verify ride was finished successfully even with zero fare
    finished_ride = await ride_repo.get_by_ride_id(ride_id)
    assert finished_ride.status == RideStatus.COMPLETED
    assert finished_ride.fare == 0.0
    assert finished_ride.HasField("finished_at")


async def test_finish_ride_payment_processing(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that payment processing occurs during finish_ride"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_with_fare(
        app_test_client, get_account_info, get_ride_request, context
    )

    # Get the ride to check fare
    ride_repo = context._mock_ride_repo
    ride = await ride_repo.get_by_ride_id(ride_id)
    expected_fare = ride.fare

    # Mock the payment gateway to track calls
    with patch(
        "example.guber.tests.mocks.MockPaymentGateway.process_payment"
    ) as mock_payment:
        mock_payment.return_value = {
            "status": "success",
            "transaction_id": "test_tx_456",
        }

        # Finish the ride
        await app_test_client.run(
            func=finish_ride,
            request=StringValue(value=ride_id),
            context=context,
        )

        # Verify payment was processed with correct data
        mock_payment.assert_called_once_with(
            {"rideId": ride_id, "amount": expected_fare}
        )

    # Verify ride was completed
    finished_ride = await ride_repo.get_by_ride_id(ride_id)
    assert finished_ride.status == RideStatus.COMPLETED
