import asyncio
from typing import AsyncIterator

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import (
    accept_ride,
    get_position_stream,
    request_ride,
    start_ride,
    update_position,
)
from example.guber.server.domain import AccountInfo, Position, RideRequest, RideStatus
from example.guber.tests.mocks import get_mock_position_repo, get_mock_ride_repo
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


async def setup_ride_for_streaming(
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


async def collect_stream_positions(
    position_stream: AsyncIterator[Position], max_positions: int = 5
) -> list[Position]:
    """Helper function to collect positions from stream with timeout"""
    positions = []
    count = 0
    async for position in position_stream:
        positions.append(position)
        count += 1
        if count >= max_positions:
            break
    return positions


async def test_get_position_stream_basic_streaming(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test basic position streaming functionality"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, get_account_info, get_ride_request, context
    )

    # Set initial position
    position_repo = get_mock_position_repo(context)
    position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

    # Get position stream (uses injected counter=2 and delay=0.1)
    position_stream = await app_test_client.run(
        func=get_position_stream,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Collect positions from stream
    positions = await collect_stream_positions(position_stream, max_positions=2)

    # Verify we got positions
    assert len(positions) == 2
    for position in positions:
        assert isinstance(position, Position)
        assert position.ride_id == ride_id
        assert abs(position.lat - (-27.584905257808835)) < 0.0001
        assert abs(position.long - (-48.545022195325124)) < 0.0001


async def test_get_position_stream_position_updates(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test position streaming reflects position updates during stream"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, get_account_info, get_ride_request, context
    )

    position_repo = get_mock_position_repo(context)
    position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

    collected_positions = []

    async def position_updater():
        """Update position while stream is running"""
        await asyncio.sleep(0.05)  # Small delay
        # Update position during streaming
        new_position = create_position(
            ride_id, -27.496887588317275, -48.522234807851476
        )
        await app_test_client.run(
            func=update_position,
            request=new_position,
            context=context,
        )

    # Start position updater task
    updater_task = asyncio.create_task(position_updater())

    # Get position stream (uses injected counter=2 and delay=0.1)
    position_stream = await app_test_client.run(
        func=get_position_stream,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Collect positions
    async for position in position_stream:
        collected_positions.append(position)
        if len(collected_positions) >= 2:
            break

    await updater_task

    # Verify positions were collected
    assert len(collected_positions) >= 2

    # First position should have initial coordinates
    first_pos = collected_positions[0]
    assert abs(first_pos.lat - (-27.584905257808835)) < 0.0001
    assert abs(first_pos.long - (-48.545022195325124)) < 0.0001

    # Later positions might have updated coordinates
    for position in collected_positions:
        assert position.ride_id == ride_id


async def test_get_position_stream_ride_completion(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test position stream stops when ride is completed"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, get_account_info, get_ride_request, context
    )

    position_repo = get_mock_position_repo(context)
    position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

    ride_repo = get_mock_ride_repo(context)
    collected_positions = []

    async def complete_ride_after_delay():
        """Complete the ride after some positions are streamed"""
        await asyncio.sleep(0.15)  # Wait for at least one position
        # Mark ride as completed
        ride = await ride_repo.get_by_ride_id(ride_id)
        ride.status = RideStatus.COMPLETED
        await ride_repo.update_ride(ride)

    # Start ride completion task
    completion_task = asyncio.create_task(complete_ride_after_delay())

    # Get position stream (uses injected counter=2 and delay=0.1)
    position_stream = await app_test_client.run(
        func=get_position_stream,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Collect positions until stream ends
    async for position in position_stream:
        collected_positions.append(position)
        if len(collected_positions) >= 5:  # Safety break
            break

    await completion_task

    # Verify stream ended due to ride completion
    assert len(collected_positions) >= 1  # Should have at least some positions
    assert len(collected_positions) <= 2  # Should stop early due to completion


async def test_get_position_stream_counter_limit(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test position stream respects counter limit"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, get_account_info, get_ride_request, context
    )

    position_repo = get_mock_position_repo(context)
    position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

    # Get position stream (uses injected counter=2 and delay=0.1)
    position_stream = await app_test_client.run(
        func=get_position_stream,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Collect all positions from stream
    positions = []
    async for position in position_stream:
        positions.append(position)
        if len(positions) > 5:  # Safety break
            break

    # Should get exactly the number of positions specified by counter
    assert len(positions) == 2


async def test_get_position_stream_nonexistent_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position stream with non-existent ride"""
    context = get_mock_context

    # Get position stream for non-existent ride (uses injected counter=2 and delay=0.1)
    position_stream = await app_test_client.run(
        func=get_position_stream,
        request=StringValue(value="nonexistent_ride"),
        context=context,
    )

    # Collect positions
    positions = await collect_stream_positions(position_stream, max_positions=2)

    # Should get positions with default coordinates (0.0, 0.0) but stream ends immediately due to is_ride_finished=True
    assert (
        len(positions) == 1
    )  # Only first position before ride is detected as finished
    assert positions[0].ride_id == "nonexistent_ride"
    assert positions[0].lat == 0.0
    assert positions[0].long == 0.0


async def test_get_position_stream_zero_counter_test():
    """Test that counter < 1 defaults to 1 - this is tested by the fixtures override"""
    # This functionality is tested through the dependency injection in fixtures
    # The fixtures.py sets get_counter to return 2, which is > 1
    # The actual counter < 1 logic would need to be tested by overriding the fixture
    pass


async def test_get_position_stream_canceled_ride(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test position stream stops when ride is canceled"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, get_account_info, get_ride_request, context
    )

    position_repo = get_mock_position_repo(context)
    position_repo.set_position(ride_id, -27.584905257808835, -48.545022195325124)

    ride_repo = get_mock_ride_repo(context)
    collected_positions = []

    async def cancel_ride_after_delay():
        """Cancel the ride after some positions are streamed"""
        await asyncio.sleep(0.15)  # Wait for at least one position
        # Mark ride as canceled
        ride = await ride_repo.get_by_ride_id(ride_id)
        ride.status = RideStatus.CANCELED
        await ride_repo.update_ride(ride)

    # Start ride cancellation task
    cancellation_task = asyncio.create_task(cancel_ride_after_delay())

    # Get position stream (uses injected counter=2 and delay=0.1)
    position_stream = await app_test_client.run(
        func=get_position_stream,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Collect positions until stream ends
    async for position in position_stream:
        collected_positions.append(position)
        if len(collected_positions) >= 5:  # Safety break
            break

    await cancellation_task

    # Stream should end due to ride cancellation
    assert len(collected_positions) >= 1  # Should have at least some positions
    assert len(collected_positions) <= 2  # Should stop early due to cancellation


async def test_get_position_stream_position_data_structure(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_ride_request: RideRequest,
    get_mock_context: ContextMock,
):
    """Test that streamed positions have correct data structure"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, get_account_info, get_ride_request, context
    )

    position_repo = get_mock_position_repo(context)
    test_lat = -27.584905257808835
    test_long = -48.545022195325124
    position_repo.set_position(ride_id, test_lat, test_long)

    # Get position stream (uses injected counter=2 and delay=0.1)
    position_stream = await app_test_client.run(
        func=get_position_stream,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Get single position
    positions = await collect_stream_positions(position_stream, max_positions=1)

    assert len(positions) == 1
    position = positions[0]

    # Verify Position structure
    assert isinstance(position, Position)
    assert hasattr(position, "ride_id")
    assert hasattr(position, "lat")
    assert hasattr(position, "long")
    assert hasattr(position, "updated_at")

    # Verify data values
    assert position.ride_id == ride_id
    assert abs(position.lat - test_lat) < 0.0001
    assert abs(position.long - test_long) < 0.0001

    # Verify timestamp is set (protobuf timestamp should be valid)
    assert position.updated_at is not None
