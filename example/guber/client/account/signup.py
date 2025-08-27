import argparse
import random
from typing import Optional

import grpc

from example.guber.client.channel import get_channel
from example.guber.server.domain import AccountInfo
from grpcAPI.protobuf import StringValue


def signup(
    channel: grpc.Channel,
    name: str,
    email: Optional[str] = None,
    sin: Optional[str] = None,
    car_plate: Optional[str] = None,
) -> str:
    method_name = "/account.account_services/signup_account"
    stub = channel.unary_unary(
        method_name,
        request_serializer=AccountInfo.SerializeToString,
        response_deserializer=StringValue.FromString,
        _registered_method=True,
    )
    email = email or name.replace(" ", ".").lower() + "@example.com"
    sin = sin or get_unique_sin()
    car_plate = car_plate or ""
    request = AccountInfo(
        name=name,
        email=email,
        sin=sin,
        car_plate=car_plate,
        is_driver=bool(car_plate),
    )
    account_id = stub(request)
    print(f"Account created with ID: {account_id.value}")
    return account_id.value


min_val = 0
max_val = 500
_counter = random.randint(min_val, max_val)


def get_unique_sin() -> str:
    global _counter
    _counter += 1

    base_number = (
        10000000 + (_counter * 7) % 89999999
    )  # Ensure 8 digits, avoid patterns
    base_str = str(base_number)[:8]  # Take first 8 digits

    return _generate_valid_sin(base_str)


def _generate_valid_sin(base: str) -> str:
    if len(base) != 8:
        raise ValueError("Base must be 8 digits")

    for check_digit in range(10):
        candidate = base + str(check_digit)
        if _luhn_check(candidate):
            return candidate

    raise ValueError(f"Could not generate valid SIN for base {base}")


def _luhn_check(number: str) -> bool:
    digits = [int(d) for d in number]
    checksum = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:  # even positions (0-based)
            dbl = d * 2
            checksum += dbl if dbl < 10 else dbl - 9
        else:
            checksum += d
    return checksum % 10 == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sign up for a new account")
    parser.add_argument("--name", required=True, help="Name of the user")
    parser.add_argument("--email", required=False, help="Email of the user")
    parser.add_argument("--sin", required=False, help="SIN of the user")
    parser.add_argument("--car_plate", required=False, help="Car plate of the user")
    args = parser.parse_args()

    with get_channel() as channel:
        signup(
            channel,
            name=args.name,
            email=args.email,
            sin=args.sin,
            car_plate=args.car_plate,
        )
