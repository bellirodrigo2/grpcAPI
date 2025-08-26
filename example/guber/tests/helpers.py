from typing import Optional

from example.guber.server.domain import AccountInfo, Coord, Position, RideRequest


def create_account_info(
    name: Optional[str] = None,
    email: Optional[str] = None,
    sin: Optional[str] = None,
    car_plate: Optional[str] = None,
    is_driver: Optional[bool] = None,
) -> AccountInfo:
    name = name if name is not None else "Test User"
    email = email if email is not None else "test@example.com"
    sin = sin if sin is not None else "046454286"

    # Set car_plate based on driver status if not provided
    if car_plate is None:
        car_plate = "ABC-1234" if is_driver else ""
    is_driver = bool(car_plate)

    return AccountInfo(
        name=name,
        email=email,
        sin=sin,
        car_plate=car_plate,
        is_driver=is_driver,
    )


def create_passenger_info(
    name: Optional[str] = None,
    email: Optional[str] = None,
    sin: Optional[str] = None,
) -> AccountInfo:
    return create_account_info(
        name=name if name is not None else "Test Passenger",
        email=email if email is not None else "passenger@test.com",
        sin=sin if sin is not None else "123456789",
        car_plate="",
        is_driver=False,
    )


def create_driver_info(
    name: Optional[str] = None,
    email: Optional[str] = None,
    sin: Optional[str] = None,
    car_plate: Optional[str] = None,
) -> AccountInfo:
    return create_account_info(
        name=name if name is not None else "Test Driver",
        email=email if email is not None else "driver@test.com",
        sin=sin if sin is not None else "123456782",
        car_plate=car_plate if car_plate is not None else "DEF-5678",
        is_driver=True,
    )


def create_coord(
    lat: Optional[float] = None,
    long: Optional[float] = None,
) -> Coord:
    return Coord(
        lat=lat if lat is not None else -27.584905257808835,
        long=long if long is not None else -48.545022195325124,
    )


def create_end_coord(
    lat: Optional[float] = None,
    long: Optional[float] = None,
) -> Coord:
    return Coord(
        lat=lat if lat is not None else -27.496887588317275,
        long=long if long is not None else -48.522234807851476,
    )


def create_ride_request(
    passenger_id: Optional[str] = None,
    start_point: Optional[Coord] = None,
    end_point: Optional[Coord] = None,
) -> RideRequest:
    return RideRequest(
        passenger_id=passenger_id if passenger_id is not None else "test_passenger_id",
        start_point=start_point if start_point is not None else create_coord(),
        end_point=end_point if end_point is not None else create_end_coord(),
    )


def create_position(ride_id: str, lat: float, long: float, timestamp_offset_seconds: float = 0.0) -> Position:
    position = Position()
    position.ride_id = ride_id
    position.coord.lat = lat
    position.coord.long = long
    if timestamp_offset_seconds == 0.0:
        position.updated_at.GetCurrentTime()
    else:
        from datetime import datetime, timedelta
        timestamp = datetime.now() + timedelta(seconds=timestamp_offset_seconds)
        position.updated_at.FromDatetime(timestamp)
    return position


# Predefined common locations for convenience
FLORIANOPOLIS_START = create_coord(-27.584905257808835, -48.545022195325124)
FLORIANOPOLIS_END = create_coord(-27.496887588317275, -48.522234807851476)
SAO_PAULO_START = create_coord(-23.550520, -46.633309)
SAO_PAULO_END = create_coord(-23.561414, -46.656166)
RIO_START = create_coord(-22.906847, -43.172896)
RIO_END = create_coord(-22.970722, -43.182365)


# Valid SIN numbers for testing (pass Luhn check)
VALID_SINS = [
    "046454286",  # Default passenger SIN
    "123456782",  # Default driver SIN
    "012345674",  # Additional valid SIN
    "234567899",  # Additional valid SIN
    "345678908",  # Additional valid SIN
]


def _luhn_check(number: str) -> bool:
    """Check if a number passes Luhn validation (from codebase implementation)"""
    digits = [int(d) for d in number]
    checksum = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:  # even positions (0-based)
            dbl = d * 2
            checksum += dbl if dbl < 10 else dbl - 9
        else:
            checksum += d
    return checksum % 10 == 0


def _generate_valid_sin(base: str) -> str:
    """Generate a valid SIN by calculating correct checksum digit"""
    if len(base) != 8:
        raise ValueError("Base must be 8 digits")

    for check_digit in range(10):
        candidate = base + str(check_digit)
        if _luhn_check(candidate):
            return candidate

    raise ValueError(f"Could not generate valid SIN for base {base}")


# Test coordinate constants for consistent assertions
EXPECTED_END_LAT = -27.496887588317275
EXPECTED_END_LONG = -48.522234807851476

# Global counter with thread safety for uniqueness across all tests
import threading
_sin_lock = threading.Lock()
_email_lock = threading.Lock()
_global_sin_counter = 0
_global_email_counter = 0


def get_unique_sin(index: int = 0) -> str:
    """
    Get a unique valid SIN for testing.

    Generates valid SINs that pass Luhn validation using thread-safe counter.
    
    Args:
        index: Index to generate unique SIN (DEPRECATED - use global counter)

    Returns:
        A valid SIN that passes validation
    """
    global _global_sin_counter
    
    # Thread-safe counter increment
    with _sin_lock:
        effective_index = _global_sin_counter
        _global_sin_counter += 1
    
    # Generate SIN directly from counter - no pre-defined list to avoid collisions
    # Use counter to create unique 8-digit base, then calculate check digit
    base_number = 10000000 + (effective_index * 7) % 89999999  # Ensure 8 digits, avoid patterns
    base_str = str(base_number)[:8]  # Take first 8 digits
    
    return _generate_valid_sin(base_str)


def get_unique_email(prefix: str = "test", index: int = 0) -> str:
    """
    Get a unique email for testing.

    Uses global counter to ensure uniqueness across ALL tests.

    Args:
        prefix: Email prefix (default: "test")
        index: Index to make email unique (DEPRECATED - use global counter)

    Returns:
        A unique email address
    """
    global _global_email_counter

    # Thread-safe counter increment
    with _email_lock:
        effective_index = _global_email_counter
        _global_email_counter += 1

    return f"{prefix}{effective_index}@example.com"


def get_unique_car_plate(index: int = 0) -> str:
    """
    Get a unique car plate for testing.

    Args:
        index: Index to make plate unique

    Returns:
        A unique car plate in valid format
    """
    plates = ["ABC-1234", "DEF-5678", "GHI-9012", "JKL-3456", "MNO-7890"]
    return plates[index % len(plates)]
