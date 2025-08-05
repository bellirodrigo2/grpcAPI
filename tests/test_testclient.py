from typing import Any as Any
from typing import Dict

import pytest

from grpcAPI import ErrorCode
from grpcAPI.app import APIService
from grpcAPI.testclient import ContextMock, TestClient
from tests.conftest import AccountInput, AsyncIt, ListValue, StringValue, Timestamp


@pytest.mark.asyncio
async def test_unary(
    testclient_fixture: TestClient,
    account_input: Dict[str, Any],
    functional_service: APIService,
) -> None:

    name = account_input["name"]
    email = account_input["email"]
    country = account_input["country"]
    itens = account_input["itens"]
    request = account_input["request"]
    inner = account_input["inner_str"]
    create_acount = None

    for method in functional_service.methods:
        if method.name == "create_account":
            create_acount = method.method
            break
    resp = await testclient_fixture.run(create_acount, request)
    assert resp.id == f"id:{name}-{email}-{country}-{itens[0]}{inner}"
    assert resp.created_at == Timestamp(seconds=1577836800)


@pytest.mark.asyncio
async def test_unary_validation(
    testclient_fixture: TestClient,
    account_input: Dict[str, Any],
    functional_service: APIService,
) -> None:

    request = account_input["request"]
    itens = request.itens
    itens.extend(["foo", "bar", "too", "much"])
    for method in functional_service.methods:
        if method.name == "create_account":
            create_acount = method.method
            break
    with pytest.raises(ValueError):
        await testclient_fixture.run(create_acount, request)


@pytest.mark.asyncio
async def test_unary_handled_error(testclient_fixture: TestClient) -> None:

    name = "raise"
    request = AccountInput(name=name)
    context = ContextMock()

    with pytest.raises(RuntimeError):
        await testclient_fixture.run_by_label(
            "", "functional", "create_account", request, context
        )

    context.tracker.set_code.assert_called_once_with(500)
    context.tracker.abort.assert_called_once_with(
        ErrorCode.ABORTED, "Not Implemented Test", ()
    )


@pytest.mark.asyncio
async def test_unary_unhandled_error(testclient_fixture: TestClient) -> None:

    name = "abort"
    request = AccountInput(name=name)
    context = ContextMock()

    with pytest.raises(RuntimeError):
        await testclient_fixture.run_by_label(
            "", "functional", "create_account", request, context
        )

    context.tracker.abort.assert_called_once()


@pytest.mark.asyncio
async def test_server_stream(testclient_fixture: TestClient) -> None:

    names = ListValue()
    list_ = ["foo", "bar"]
    names.extend(list_)

    context = ContextMock()

    resp = await testclient_fixture.run_by_label(
        "", "functional", "get_accounts", names, context
    )
    accounts = [acc async for acc in resp]

    context.tracker.peer.assert_called_once()
    context.tracker.set_code.assert_called_once_with("bar")

    for name, acc in zip(list_, accounts):
        assert acc.name == name
        assert acc.email == f"{name}@email.com"

    names.extend(["abort"])
    resp = await testclient_fixture.run_by_label(
        "", "functional", "get_accounts", names, context
    )
    with pytest.raises(RuntimeError):
        accounts = [acc async for acc in resp]


@pytest.mark.asyncio
async def test_server_stream_with_error(testclient_fixture: TestClient) -> None:

    names = ListValue()
    list_ = [
        "raise",
    ]
    names.extend(list_)

    context = ContextMock()

    resp = await testclient_fixture.run_by_label(
        "", "functional", "get_accounts", names, context
    )
    with pytest.raises(RuntimeError):
        [acc async for acc in resp]

    context.tracker.set_code.assert_called_once_with(500)
    context.tracker.abort.assert_called_once_with(
        ErrorCode.ABORTED, "Not Implemented Test", ()
    )


@pytest.mark.asyncio
async def test_bilateral(testclient_fixture: TestClient) -> None:

    def sv(v: str) -> StringValue:
        return StringValue(value=v)

    name_values = [sv("foo"), sv("bar")]
    names = AsyncIt(name_values)
    resp = await testclient_fixture.run_by_label("", "functional", "get_by_ids", names)

    async for acc in resp:
        assert acc.name.startswith("account")
        assert acc.name[7:] in ["foo", "bar"]
        assert acc.email.endswith("@email.com")
