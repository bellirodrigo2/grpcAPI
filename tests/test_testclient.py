import pytest
from google.protobuf.struct_pb2 import Struct

from grpcAPI.testclient.contextmock import ContextMock
from grpcAPI.testclient.testclient import TestClient
from tests.conftest import AccountInput, AsyncIt, ListValue, StringValue, Timestamp


@pytest.mark.asyncio
async def test_unary(testclient_fixture: TestClient) -> None:

    name = "John"
    email = "john@email.com"
    country = "BR"
    struct = Struct()
    struct.update({"country": country, "size": 125})
    itens = ListValue()
    l = ["foo"]
    itens.extend(l)

    request = AccountInput(name=name, email=email, payload=struct, itens=itens)

    resp = await testclient_fixture.run_by_label(
        "", "functional", "create_account", request
    )
    assert resp.id == f"id:{name}-{email}-{country}-{l[0]}"
    assert resp.created_at == Timestamp(seconds=1577836800)


@pytest.mark.asyncio
async def test_server_stream(testclient_fixture: TestClient) -> None:

    names = ListValue()
    l = ["foo", "bar"]
    names.extend(l)

    context = ContextMock()

    resp = await testclient_fixture.run_by_label(
        "", "functional", "get_accounts", names, context
    )
    accounts = [acc async for acc in resp]

    context.tracker.peer.assert_called_once()
    context.tracker.set_code.assert_called_once_with("bar")

    for name, acc in zip(l, accounts):
        assert acc.name == name
        assert acc.email == f"{name}@email.com"

    names.extend(["abort"])
    resp = await testclient_fixture.run_by_label(
        "", "functional", "get_accounts", names, context
    )
    with pytest.raises(RuntimeError):
        accounts = [acc async for acc in resp]


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
