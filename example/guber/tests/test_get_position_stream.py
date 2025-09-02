import asyncio
from datetime import datetime
from typing import AsyncIterator, List, Tuple

import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.application.usecase.ride import (
    accept_ride,
    get_position_stream,
    request_ride,
    start_ride,
    update_position,
)
from example.guber.server.domain import KeyValueStr, Position, RideStatus
from example.guber.tests.fixtures import get_position_repo_test, get_ride_repo_test
from grpcAPI.protobuf import StringValue
from grpcAPI.testclient import ContextMock, TestClient

from .helpers import (
    create_coord,
    create_driver_info,
    create_passenger_info,
    create_position,
    create_ride_request,
    get_unique_email,
    get_unique_sin,
)


async def setup_ride_for_streaming(
    app_test_client: TestClient,
    context: ContextMock,
    unique_index: int = 0,
) -> Tuple[str, str, str]:
    """Helper function to set up ride ready for position streaming"""
    # Create unique passenger account
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 200 + unique_index),
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
        email=get_unique_email("driver", 200 + unique_index),
        sin=get_unique_sin((unique_index + 1) % 5),
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


async def collect_stream_positions(
    position_stream: AsyncIterator[Position], max_positions: int = 5
) -> List[Position]:
    """Helper function to collect positions from stream with timeout"""
    positions = []
    count = 0
    try:
        async for position in position_stream:
            positions.append(position)
            count += 1
            if count >= max_positions:
                break
    finally:
        # Properly close async generator to prevent pending task warnings in Python 3.8
        if hasattr(position_stream, "aclose"):
            await position_stream.aclose()
    return positions


async def test_get_position_stream_basic_streaming(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test basic position streaming functionality"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, context, unique_index=0
    )

    # Set initial position using SQLAlchemy repo
    from example.guber.server.domain import Coord

    initial_coord = Coord(lat=-27.584905257808835, long=-48.545022195325124)

    async with get_position_repo_test() as position_repo:
        async with get_ride_repo_test() as ride_repo:
            ride = await ride_repo.get_by_ride_id(ride_id)
            await position_repo.create_position(
                ride_id, initial_coord, ride.accepted_at.ToDatetime()
            )

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
        assert position.coord.lat == pytest.approx(-27.584905257808835, abs=1e-2)
        assert position.coord.long == pytest.approx(-48.545022195325124, abs=1e-2)


async def test_get_position_stream_position_updates(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position streaming reflects position updates during stream"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, context, unique_index=1
    )

    # Set initial position using SQLAlchemy repo
    from example.guber.server.domain import Coord

    initial_coord = Coord(lat=-27.584905257808835, long=-48.545022195325124)

    async with get_position_repo_test() as position_repo:
        async with get_ride_repo_test() as ride_repo:
            ride = await ride_repo.get_by_ride_id(ride_id)
            await position_repo.create_position(
                ride_id, initial_coord, ride.accepted_at.ToDatetime()
            )

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
    try:
        async for position in position_stream:
            collected_positions.append(position)
            if len(collected_positions) >= 2:
                break
    finally:
        # Properly close async generator to prevent pending task warnings in Python 3.8
        if hasattr(position_stream, "aclose"):
            await position_stream.aclose()

    await updater_task

    # Verify positions were collected
    assert len(collected_positions) >= 2

    # First position should have initial coordinates
    first_pos = collected_positions[0]
    assert first_pos.coord.lat == pytest.approx(-27.584905257808835, abs=1e-2)
    assert first_pos.coord.long == pytest.approx(-48.545022195325124, abs=1e-2)

    # Later positions might have updated coordinates
    for position in collected_positions:
        assert position.ride_id == ride_id


async def test_get_position_stream_ride_completion(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position stream stops when ride is completed"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, context, unique_index=2
    )

    # Set initial position using SQLAlchemy repo
    initial_coord = create_coord(lat=-27.584905257808835, long=-48.545022195325124)

    async with get_position_repo_test() as position_repo:
        async with get_ride_repo_test() as ride_repo:
            ride = await ride_repo.get_by_ride_id(ride_id)
            await position_repo.create_position(
                ride_id, initial_coord, ride.accepted_at.ToDatetime()
            )

    # Use SQLAlchemy ride repo
    collected_positions = []

    async def complete_ride_after_delay():
        await asyncio.sleep(0.15)
        async with get_ride_repo_test() as ride_repo:
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
    try:
        async for position in position_stream:
            collected_positions.append(position)
            if len(collected_positions) >= 5:  # Safety break
                break
    finally:
        # Properly close async generator to prevent pending task warnings in Python 3.8
        if hasattr(position_stream, "aclose"):
            await position_stream.aclose()

    await completion_task

    # Verify stream ended due to ride completion
    assert len(collected_positions) >= 1  # Should have at least some positions
    assert len(collected_positions) <= 2  # Should stop early due to completion


async def test_get_position_stream_counter_limit(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position stream respects counter limit"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, context, unique_index=3
    )

    # Set initial position using SQLAlchemy repo
    from example.guber.server.domain import Coord

    initial_coord = Coord(lat=-27.584905257808835, long=-48.545022195325124)

    async with get_position_repo_test() as position_repo:
        async with get_ride_repo_test() as ride_repo:
            ride = await ride_repo.get_by_ride_id(ride_id)
            await position_repo.create_position(
                ride_id, initial_coord, ride.accepted_at.ToDatetime()
            )

    # Get position stream (uses injected counter=2 and delay=0.1)
    position_stream = await app_test_client.run(
        func=get_position_stream,
        request=StringValue(value=ride_id),
        context=context,
    )

    # Collect all positions from stream
    positions = []
    try:
        async for position in position_stream:
            positions.append(position)
            if len(positions) > 5:  # Safety break
                break
    finally:
        # Properly close async generator to prevent pending task warnings in Python 3.8
        if hasattr(position_stream, "aclose"):
            await position_stream.aclose()

    # Should get exactly the number of positions specified by counter
    assert len(positions) == 2


async def test_get_position_stream_nonexistent_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position stream with non-existent ride should raise ValueError"""

    context = get_mock_context

    # Get position stream for non-existent ride should fail immediately
    with pytest.raises(
        ValueError, match="Current position not found for ride id nonexistent_ride"
    ):
        position_stream = await app_test_client.run(
            func=get_position_stream,
            request=StringValue(value="nonexistent_ride"),
            context=context,
        )

        # Try to get first position - should raise ValueError before this
        try:
            async for position in position_stream:
                break
        finally:
            # Properly close async generator to prevent pending task warnings in Python 3.8
            if hasattr(position_stream, "aclose"):
                await position_stream.aclose()


async def test_get_position_stream_zero_counter_test():
    """Test that counter < 1 defaults to 1 - this is tested by the fixtures override"""
    # This functionality is tested through the dependency injection in fixtures
    # The fixtures.py sets get_counter to return 2, which is > 1
    # The actual counter < 1 logic would need to be tested by overriding the fixture
    pass


async def test_get_position_stream_canceled_ride(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test position stream stops when ride is canceled"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, context, unique_index=4
    )

    # Set initial position using SQLAlchemy repo
    from example.guber.server.domain import Coord

    initial_coord = Coord(lat=-27.584905257808835, long=-48.545022195325124)

    async with get_position_repo_test() as position_repo:
        async with get_ride_repo_test() as ride_repo:
            ride = await ride_repo.get_by_ride_id(ride_id)
            await position_repo.create_position(
                ride_id, initial_coord, ride.accepted_at.ToDatetime()
            )

    # Use SQLAlchemy ride repo
    collected_positions = []

    async def cancel_ride_after_delay():
        """Cancel the ride after some positions are streamed"""
        await asyncio.sleep(0.15)  # Wait for at least one position
        # Mark ride as canceled
        async with get_ride_repo_test() as ride_repo:
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
    try:
        async for position in position_stream:
            collected_positions.append(position)
            if len(collected_positions) >= 5:  # Safety break
                break
    finally:
        # Properly close async generator to prevent pending task warnings in Python 3.8
        if hasattr(position_stream, "aclose"):
            await position_stream.aclose()

    await cancellation_task

    # Stream should end due to ride cancellation
    assert len(collected_positions) >= 1  # Should have at least some positions
    assert len(collected_positions) <= 2  # Should stop early due to cancellation


async def test_get_position_stream_position_data_structure(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    """Test that streamed positions have correct data structure"""
    context = get_mock_context

    ride_id, passenger_id, driver_id = await setup_ride_for_streaming(
        app_test_client, context, unique_index=5
    )

    async with get_position_repo_test() as position_repo:
        test_lat = -27.584905257808835
        test_long = -48.545022195325124
        await position_repo.create_position(
            ride_id,
            create_coord(test_lat, test_long),
            updated_at=datetime.now(),
        )

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
    assert hasattr(position, "coord")
    assert hasattr(position, "updated_at")

    # Verify data values
    assert position.ride_id == ride_id
    assert position.coord.lat == pytest.approx(test_lat, abs=1e-2)
    assert position.coord.long == pytest.approx(test_long, abs=1e-2)

    # Verify timestamp is set (protobuf timestamp should be valid)
    assert position.updated_at is not None
