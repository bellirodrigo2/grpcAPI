from unittest.mock import MagicMock

import pytest
from typing_extensions import Any, Dict

from grpcAPI.add_to_server import add_to_server
from grpcAPI.app import APIService
from grpcAPI.commands.process_service.inject_typing import InjectProtoTyping
from grpcAPI.server import ServerWrapper
from grpcAPI.testclient.contextmock import ContextMock
from tests.conftest import Timestamp
from tests.lib.account_pb2 import AccountInput


@pytest.fixture
def mock_server() -> ServerWrapper:
    return ServerWrapper(server=MagicMock())


@pytest.mark.asyncio
async def test_add_simple(
    mock_server: ServerWrapper,
    functional_service: APIService,
    account_input: Dict[str, Any],
) -> None:
    inject_proto_processing = InjectProtoTyping()
    inject_proto_processing.process(functional_service)
    methods = add_to_server(functional_service, mock_server, {}, {})
    assert set(methods.keys()) == set(
        ["create_account", "get_accounts", "get_by_ids", "get_emails"]
    )
    request = account_input["request"]
    context = ContextMock()
    resp = await methods["create_account"](request, context)
    assert resp.created_at == Timestamp(seconds=1577836800)

    mock_server._server.add_generic_rpc_handlers.assert_called_once()
    mock_server._server.add_registered_method_handlers.assert_called_once()

    req2 = AccountInput()
    req2.CopyFrom(request)
    req2.name = "abort"
    with pytest.raises(RuntimeError):
        resp = await methods["create_account"](req2, context)
