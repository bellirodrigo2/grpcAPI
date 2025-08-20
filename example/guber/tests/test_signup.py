import pytest

from example.guber.server.application.usecase.account import signup_account
from example.guber.server.domain import AccountInfo
from grpcAPI.testclient import ContextMock, TestClient

pytest_plugins = ["example.guber.tests.fixtures"]


async def test_signup_passenger(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_mock_context: ContextMock,
):
    context = get_mock_context
    get_account_info.car_plate = ""  # Passengers do not have car plates
    get_account_info.is_driver = False  # Passengers are not drivers
    resp = await app_test_client.run(
        func=signup_account,
        request=get_account_info,
        context=context,
    )
    assert resp.value.startswith("test_account_id_")
    context.tracker.invocation_metadata.assert_called_once()
    account_repo = context._mockrepo

    assert account_repo.calls[0] == ("exist_sin", "046454286")
    assert account_repo.calls[1] == ("exist_email", "test@example.com")
    account_id = resp.value
    assert account_repo.calls[2] == (
        "create_account",
        account_id,
        get_account_info,
    )
    account = await account_repo.get_by_id(account_id)
    assert account is not None
    assert account.info.name == "Test User"
    assert account.info.email == "test@example.com"
    assert account.info.sin == "046454286"
    assert account.info.car_plate == ""
    assert account.info.is_driver is False


async def test_signup_driver(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_mock_context: ContextMock,
):
    driver_info = get_account_info
    driver_info.car_plate = "DEF-5678"
    driver_info.is_driver = True

    context = get_mock_context
    resp = await app_test_client.run(
        func=signup_account,
        request=driver_info,
        context=context,
    )
    assert resp.value.startswith("test_account_id_")
    account_repo = context._mockrepo
    account_id = resp.value
    account = await account_repo.get_by_id(account_id)
    assert account is not None
    assert account.info.car_plate == "DEF-5678"
    assert account.info.is_driver is True


async def test_signup_invalid_email(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_mock_context: ContextMock,
):
    invalid_email_info = get_account_info
    invalid_email_info.email = "invalid-email"

    context = get_mock_context
    with pytest.raises(Exception):  # Email validation should fail
        await app_test_client.run(
            func=signup_account,
            request=invalid_email_info,
            context=context,
        )


async def test_signup_invalid_sin(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_mock_context: ContextMock,
):
    invalid_sin_info = get_account_info
    invalid_sin_info.sin = "123456789012345"  # Invalid SIN - too long

    context = get_mock_context
    with pytest.raises(ValueError):  # SIN validation should fail
        await app_test_client.run(
            func=signup_account,
            request=invalid_sin_info,
            context=context,
        )


async def test_signup_duplicate_email(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_mock_context: ContextMock,
):
    context = get_mock_context
    # First signup should succeed
    await app_test_client.run(
        func=signup_account,
        request=get_account_info,
        context=context,
    )

    with pytest.raises(
        ValueError,
    ):
        await app_test_client.run(
            func=signup_account,
            request=get_account_info,
            context=context,
        )


async def test_signup_invalid_car_plate(
    app_test_client: TestClient,
    get_account_info: AccountInfo,
    get_mock_context: ContextMock,
):
    invalid_plate_info = get_account_info
    invalid_plate_info.car_plate = "INVALID"  # Invalid car plate format

    context = get_mock_context
    with pytest.raises(ValueError):  # Car plate validation should fail
        await app_test_client.run(
            func=signup_account,
            request=invalid_plate_info,
            context=context,
        )
