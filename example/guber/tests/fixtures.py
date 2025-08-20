from typing import Any, Dict, Generator

import pytest

from example.guber.server.app import app
from example.guber.server.application.gateway import get_payment_gateway
from example.guber.server.application.gateway.auth import async_authentication
from example.guber.server.application.internal_access import (
    is_passenger,
    passenger_name,
)
from example.guber.server.application.repo.account_repo import get_account_repo
from example.guber.server.application.repo.position_repo import get_position_repo
from example.guber.server.application.repo.ride_repo import get_ride_repo
from example.guber.server.application.usecase.ride import get_counter, get_delay
from example.guber.server.domain.entity.account_rules import make_account_id
from example.guber.server.domain.entity.lib.account.account_proto_pb2 import AccountInfo
from example.guber.server.domain.entity.lib.ride.ride_proto_pb2 import RideRequest
from grpcAPI.app import App
from grpcAPI.testclient.contextmock import ContextMock
from grpcAPI.testclient.testclient import TestClient

from .mocks import (
    get_mock_account_repo,
    get_mock_authentication,
    get_mock_is_passenger,
    get_mock_passenger_name,
    get_mock_payment_gateway,
    get_mock_position_repo,
    get_mock_ride_repo,
)


def make_unique_account_id():
    counter = 0

    def _generate_id():
        nonlocal counter
        counter += 1
        return f"test_account_id_{counter}"

    return _generate_id


@pytest.fixture
def guber_test_app() -> Generator[App, Any, None]:
    app.dependency_overrides[make_account_id] = make_unique_account_id()
    app.dependency_overrides[async_authentication] = get_mock_authentication
    app.dependency_overrides[is_passenger] = get_mock_is_passenger
    app.dependency_overrides[get_counter] = lambda: 2  # choose you number here
    app.dependency_overrides[get_delay] = lambda: 0.1
    app.dependency_overrides[passenger_name] = get_mock_passenger_name
    app.dependency_overrides[get_payment_gateway] = get_mock_payment_gateway
    app.dependency_overrides[get_account_repo] = get_mock_account_repo
    app.dependency_overrides[get_ride_repo] = get_mock_ride_repo
    app.dependency_overrides[get_position_repo] = get_mock_position_repo

    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def app_settings() -> Dict[str, Any]:
    return {}


@pytest.fixture
def app_test_client(guber_test_app: App, app_settings: Dict[str, Any]):
    testclient = TestClient(guber_test_app, app_settings)
    yield testclient


@pytest.fixture
def get_mock_context():
    context = ContextMock()
    context.set_trailing_metadata([("user", "John"), ("password", "test_password")])
    return context


@pytest.fixture
def get_account_info():
    return AccountInfo(
        name="Test User",
        email="test@example.com",
        sin="046454286",
        car_plate="ABC-1234",
        is_driver=True,
    )


@pytest.fixture
def get_ride_request():
    return RideRequest(
        passenger_id="test_passenger_id",
        from_lat=-27.584905257808835,
        from_long=-48.545022195325124,
        to_lat=-27.496887588317275,
        to_long=-48.522234807851476,
    )


# print(is_valid_sin("046454286"))  # True
# print(is_valid_sin("123456789"))  # False
