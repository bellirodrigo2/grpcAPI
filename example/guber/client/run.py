import argparse
import asyncio
import time
from typing import Tuple
from uuid import uuid4

from example.guber.client.account import (
    get_account,
    signup,
    update_car_plate,
    update_email,
)
from example.guber.client.channel import get_async_channel, get_channel
from example.guber.client.ride import (
    accept_ride,
    finish_ride,
    get_position_stream,
    get_ride,
    request_ride,
    start_ride,
    update_position,
    update_position_stream,
)

steps_delay = 0.2


def client_account(port: str = "50051") -> Tuple[str, str]:

    passenger_id = ""
    driver_id = ""

    with get_channel(port=port) as channel:
        passenger_id = signup(
            channel,
            name=str(uuid4()),
        )
        time.sleep(steps_delay)
        get_account(channel, passenger_id)
        time.sleep(steps_delay)
        update_email(
            channel, passenger_id, f"{str(uuid4()).replace('-', '')}@example.com"
        )

        driver_id = signup(channel, name=str(uuid4()), car_plate="XYZ-1234")
        time.sleep(steps_delay)
        get_account(channel, driver_id)
        time.sleep(steps_delay)
        update_car_plate(channel, driver_id, "XYZ-9876")
        time.sleep(steps_delay)
    return passenger_id, driver_id


async def client_ride(passenger_id: str, driver_id: str, port: str = "50051") -> None:

    async with get_async_channel(port=port) as channel:
        ride_id = await request_ride(channel=channel, passenger_id=passenger_id)
        await asyncio.sleep(steps_delay)
        await get_ride(channel=channel, ride_id=ride_id)
        await asyncio.sleep(steps_delay)
        await accept_ride(channel=channel, ride_id=ride_id, driver_id=driver_id)
        await asyncio.sleep(steps_delay)
        await start_ride(channel=channel, ride_id=ride_id)
        await asyncio.sleep(steps_delay)
        await update_position(channel=channel, ride_id=ride_id, lat=10.0, lon=10.0)
        await get_ride(channel=channel, ride_id=ride_id)

        async def update():
            await update_position_stream(
                channel=channel,
                ride_id=ride_id,
                positions=[(20.0, 20.0), (30.0, 30.0), (40.0, 40.0)],
                delay=3.0,
            )

        async def position():
            await asyncio.sleep(1)
            await get_position_stream(
                channel=channel,
                ride_id=ride_id,
                delay=3.0,
                counter=4,
            )

        await asyncio.sleep(steps_delay)
        await asyncio.gather(update(), position())
        await asyncio.sleep(steps_delay)
        await get_ride(channel=channel, ride_id=ride_id)
        await asyncio.sleep(steps_delay)
        await finish_ride(channel=channel, ride_id=ride_id)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Get account information")
    parser.add_argument(
        "--port1", "-p1", type=str, default="50051", help="Port number for channel 1"
    )
    parser.add_argument(
        "--port2", "-p2", type=str, default="50051", help="Port number for channel 2"
    )

    args = parser.parse_args()

    passenger_id, driver_id = client_account(args.port1)
    asyncio.run(client_ride(passenger_id, driver_id, args.port2))
