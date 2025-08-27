from typing import Any, Dict

import pytest
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from example.guber.server.adapters.repo.sqlalchemy import (
    get_account_sqlalchemy_repo as get_account_repo_test,
)
from example.guber.server.adapters.repo.sqlalchemy import (
    get_position_sqlalchemy_repo as get_position_repo_test,
)
from example.guber.server.adapters.repo.sqlalchemy import (
    get_ride_sqlalchemy_repo as get_ride_repo_test,
)
from example.guber.server.adapters.repo.sqlalchemy.db import init_db
from example.guber.server.app import app
from example.guber.server.application.gateway import get_payment_gateway
from example.guber.server.application.repo.account_repo import get_account_repo
from example.guber.server.application.repo.position_repo import get_position_repo
from example.guber.server.application.repo.ride_repo import get_ride_repo
from example.guber.server.domain.entity.account_rules import make_account_id
from example.guber.server.domain.entity.ride_rules import make_ride_id
from grpcAPI.app import App
from grpcAPI.testclient.contextmock import ContextMock
from grpcAPI.testclient.testclient import TestClient

from .mocks import get_mock_payment_gateway


def make_unique_account_id_factory(prefix: str):
    counter = 0

    def _generate_id():
        nonlocal counter
        counter += 1
        return f"{prefix}_{counter}"

    return _generate_id


make_unique_account_id = make_unique_account_id_factory("test_account_id")
make_unique_ride_id = make_unique_account_id_factory("test_ride_id")


@pytest.fixture(scope="session")
async def test_db_engine():
    import os
    import tempfile

    # Create temp database file
    _temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    _temp_db_file.close()

    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_temp_db_file.name}"

    async with init_db(app):
        yield

    try:
        print(f"\nCleaning up temporary database file. {_temp_db_file.name}")
        os.unlink(_temp_db_file.name)
        print("Cleanup successful")
    except (FileNotFoundError, AttributeError):
        pass
    except PermissionError:
        print(f"Temp file {_temp_db_file.name} in use, will be cleaned by OS")
    except Exception as e:
        print(f"Cleanup warning: {e}")


@pytest.fixture
async def guber_test_app(test_db_engine: AsyncEngine):
    app.dependency_overrides[make_account_id] = make_unique_account_id
    app.dependency_overrides[make_ride_id] = make_unique_ride_id
    app.dependency_overrides[get_payment_gateway] = get_mock_payment_gateway

    app.dependency_overrides[get_account_repo] = get_account_repo_test
    app.dependency_overrides[get_ride_repo] = get_ride_repo_test
    app.dependency_overrides[get_position_repo] = get_position_repo_test

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
    context.set_trailing_metadata(
        [
            ("user", "John"),
            ("password", "test_password"),
            ("delay", "0.1"),
            ("counter", "2"),
        ]
    )
    return context
