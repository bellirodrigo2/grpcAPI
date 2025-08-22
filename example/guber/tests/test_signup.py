import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.domain.vo.account import validate_sin
from example.guber.tests.fixtures import get_account_repo_test
from grpcAPI.testclient import ContextMock, TestClient

from .helpers import (
    create_account_info,
    create_driver_info,
    create_passenger_info,
    get_unique_email,
    get_unique_sin,
)


async def test_signup_passenger(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    context = get_mock_context
    passenger_info = create_passenger_info(
        email=get_unique_email("passenger", 15), sin=get_unique_sin(0)
    )
    resp = await app_test_client.run(
        func=signup_account,
        request=passenger_info,
        context=context,
    )
    assert resp.value.startswith("test_account_id_")
    context.tracker.invocation_metadata.assert_called_once()

    async with get_account_repo_test() as account_repo:
        account_id = resp.value
        account = await account_repo.get_by_id(account_id)
        assert account is not None
        assert account.info.name == "Test Passenger"
        assert account.info.email.startswith("passenger")
        assert account.info.email.endswith("@example.com")
        assert bool(validate_sin(account.info.sin))
        assert account.info.car_plate == ""
        assert account.info.is_driver is False


async def test_signup_driver(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    driver_info = create_driver_info(
        email=get_unique_email("driver", 15), sin=get_unique_sin(1)
    )

    context = get_mock_context
    resp = await app_test_client.run(
        func=signup_account,
        request=driver_info,
        context=context,
    )
    assert resp.value.startswith("test_account_id_")
    async with get_account_repo_test() as account_repo:
        account_id = resp.value
        account = await account_repo.get_by_id(account_id)
        assert account is not None
        assert account.info.car_plate == "DEF-5678"
        assert account.info.is_driver is True


async def test_signup_invalid_email(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    invalid_email_info = create_account_info(
        email="invalid-email", sin=get_unique_sin(2)  # Invalid email format
    )

    context = get_mock_context
    with pytest.raises(Exception):  # Email validation should fail
        await app_test_client.run(
            func=signup_account,
            request=invalid_email_info,
            context=context,
        )


async def test_signup_invalid_sin(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    invalid_sin_info = create_account_info(
        email=get_unique_email("test", 16),
        sin="123456789012345",  # Invalid SIN - too long
    )

    context = get_mock_context
    with pytest.raises(ValueError):  # SIN validation should fail
        await app_test_client.run(
            func=signup_account,
            request=invalid_sin_info,
            context=context,
        )


async def test_signup_duplicate_email(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    context = get_mock_context

    # Create account info with unique email for this test
    duplicate_email = get_unique_email("duplicate", 17)
    account_info = create_account_info(email=duplicate_email, sin=get_unique_sin(3))

    # First signup should succeed
    await app_test_client.run(
        func=signup_account,
        request=account_info,
        context=context,
    )

    # Second signup with same email should fail
    duplicate_account_info = create_account_info(
        email=duplicate_email, sin=get_unique_sin(4)  # Same email  # Different SIN
    )
    with pytest.raises(
        ValueError,
    ):
        await app_test_client.run(
            func=signup_account,
            request=duplicate_account_info,
            context=context,
        )


async def test_signup_invalid_car_plate(
    app_test_client: TestClient,
    get_mock_context: ContextMock,
):
    invalid_plate_info = create_account_info(
        email=get_unique_email("test", 18),
        sin=get_unique_sin(0),
        car_plate="INVALID",  # Invalid car plate format
        is_driver=True,
    )

    context = get_mock_context
    with pytest.raises(ValueError):  # Car plate validation should fail
        await app_test_client.run(
            func=signup_account,
            request=invalid_plate_info,
            context=context,
        )
