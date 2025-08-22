from typing import Dict, List, Optional, Tuple

from example.guber.server.domain import (
    Account,
    AccountInfo,
    Ride,
    RideRequest,
    RideStatus,
)
from grpcAPI import AsyncContext
from grpcAPI.protobuf import Metadata


class MockAccountRepo:
    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.emails: set[str] = set()
        self.sins: set[str] = set()
        self.calls = []
        
        # Add default test accounts
        self._add_default_accounts()

    async def get_by_id(self, id: str) -> Optional[Account]:
        self.calls.append(("get_by_id", id))
        return self.accounts.get(id)

    async def exist_email(self, email: str) -> bool:
        self.calls.append(("exist_email", email))
        if email in self.emails:
            raise ValueError(f"Email {email} already exists")
        return False

    async def exist_sin(self, sin: str) -> bool:
        self.calls.append(("exist_sin", sin))
        if sin in self.sins:
            raise ValueError(f"SIN {sin} already exists")
        return False

    async def create_account(self, id: str, account_info: AccountInfo) -> str:
        self.calls.append(("create_account", id, account_info))
        account = Account(account_id=id, info=account_info)
        self.accounts[id] = account
        self.emails.add(account_info.email)
        self.sins.add(account_info.sin)
        return id

    async def list_accounts(self, ids: List[str]) -> List[Account]:
        self.calls.append(("list_accounts", ids))
        return [self.accounts[id] for id in ids if id in self.accounts]

    async def update_account_field(self, id: str, field: str, value: str) -> bool:
        self.calls.append(("update_account_field", id, field, value))
        if id not in self.accounts:
            return False
        account = self.accounts[id]
        if hasattr(account.info, field):
            setattr(account.info, field, value)
            return True
        return False
    
    def _add_default_accounts(self):
        """Add default test accounts for fixtures"""
        from example.guber.server.domain import AccountInfo, Account
        
        # Default passenger account
        passenger_info = AccountInfo(
            name="Test Passenger",
            email="passenger@test.com", 
            sin="123456789",
            car_plate="",
            is_driver=False
        )
        passenger_account = Account(account_id="test_passenger_id", info=passenger_info)
        self.accounts["test_passenger_id"] = passenger_account
        self.emails.add("passenger@test.com")
        self.sins.add("123456789")


class MockRideRepo:
    def __init__(self):
        self.rides: Dict[str, Ride] = {}
        self.active_rides: Dict[str, str] = {}  # user_id -> ride_id
        self.calls = []

    async def has_active_ride(self, user_id: str) -> bool:
        self.calls.append(("has_active_ride", user_id))
        return user_id in self.active_rides

    async def get_by_ride_id(self, ride_id: str) -> Optional[Ride]:
        self.calls.append(("get_by_ride_id", ride_id))
        return self.rides.get(ride_id)

    async def create_ride(self, request: RideRequest) -> str:
        self.calls.append(("create_ride", request))
        ride_id = f"ride_{len(self.rides) + 1}"
        ride = Ride(
            ride_id=ride_id,
            passenger_id=request.passenger_id,
            driver_id="",
            status=RideStatus.REQUESTED,
            fare=0.0,
        )
        ride.start_point.CopyFrom(request.start_point)
        ride.end_point.CopyFrom(request.end_point)
        self.rides[ride_id] = ride
        self.active_rides[request.passenger_id] = ride_id
        return ride_id

    async def update_ride(self, ride: Ride) -> None:
        self.calls.append(("update_ride", ride))
        self.rides[ride.ride_id] = ride
        if ride.status == RideStatus.ACCEPTED and ride.driver_id:
            # Add driver to active rides when ride is accepted
            self.active_rides[ride.driver_id] = ride.ride_id
        elif ride.status == RideStatus.COMPLETED:
            # Remove ALL users from active rides when completed (both passenger and driver)
            for user_id, ride_id in list(self.active_rides.items()):
                if ride_id == ride.ride_id:
                    del self.active_rides[user_id]

    async def is_ride_finished(self, ride_id: str) -> bool:
        self.calls.append(("is_ride_finished", ride_id))
        ride = self.rides.get(ride_id)
        if ride is None:
            return True  # Non-existent ride is considered finished
        return ride.status in [RideStatus.COMPLETED, RideStatus.CANCELED]


class MockPositionRepo:
    def __init__(self):
        self.positions: Dict[str, Tuple[float, float]] = {}

    async def create_position(self, ride_id: str, coord, updated_at) -> None:
        """Create an initial position for a ride"""
        self.positions[ride_id] = (coord.lat, coord.long)

    async def get_current_position(self, ride_id: str):
        from example.guber.server.domain import Position

        lat, long = self.positions.get(ride_id, (0.0, 0.0))
        position = Position()
        position.ride_id = ride_id
        position.coord.lat = lat
        position.coord.long = long
        position.updated_at.GetCurrentTime()
        return position

    def set_position(self, ride_id: str, lat: float, lng: float):
        self.positions[ride_id] = (lat, lng)

    async def update_position(self, position):
        """Update position and store it (called by update_position use case)"""
        self.positions[position.ride_id] = (position.coord.lat, position.coord.long)


def get_mock_account_repo(context: AsyncContext):
    if not hasattr(context, "_mockrepo"):
        context._mockrepo = MockAccountRepo()
    return context._mockrepo


def get_mock_ride_repo(context: AsyncContext):
    if not hasattr(context, "_mock_ride_repo"):
        context._mock_ride_repo = MockRideRepo()
    return context._mock_ride_repo


def get_mock_position_repo(context: AsyncContext):
    if not hasattr(context, "_mock_position_repo"):
        context._mock_position_repo = MockPositionRepo()
    return context._mock_position_repo


async def get_mock_authentication(metadata: Metadata) -> None:
    if "user" in metadata and "password" in metadata:
        return
    raise ValueError("Invalid metadata")




class MockPaymentGateway:
    async def process_payment(self, payment_data):
        # Mock payment processing
        return {"status": "success", "transaction_id": "mock_tx_123"}


def get_mock_payment_gateway():
    return MockPaymentGateway()
