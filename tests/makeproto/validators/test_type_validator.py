from pathlib import Path
from typing import Any, AsyncIterator, Dict

import pytest

from grpcAPI.makeproto.compiler import (
    CompilerContext,
    list_ctx_error_code,
    list_ctx_error_messages,
)
from grpcAPI.makeproto.validators.type import TypeValidator
from tests.makeproto.test_helpers import make_method, make_service


class ValidClass:
    pass


class ValidClass2:
    pass


async def agen():  # type: ignore
    yield "hello"


def not_async():  # type: ignore
    yield "hello"


async def not_gen():  # type: ignore
    return "hello"


@pytest.fixture
def validator_setup() -> Dict[str, Any]:
    return {
        "validator": TypeValidator(),
        "context": CompilerContext(),
        "block": make_service("ValidBlock"),
        "service": make_service("Service"),
    }


def test_field_no_type(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "field1", service=validator_setup["block"], requests=[], response=ValidClass
    )
    validator_setup["validator"].execute(
        [validator_setup["block"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert validator_setup["context"].has_errors()
    assert all(
        code == "E801" for code in list_ctx_error_code(validator_setup["context"])
    )


def test_method_ok_req(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[ValidClass],
        service=validator_setup["service"],
        response=ValidClass,
        method=not_gen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 0
    assert validator_setup["context"].is_valid()


def test_method_ok_stream_req(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[AsyncIterator[ValidClass]],
        service=validator_setup["service"],
        response=AsyncIterator[ValidClass],
        method=agen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 0


def test_method_empty_req(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[],
        service=validator_setup["service"],
        response=ValidClass,
        method=not_gen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert "E801" in list_ctx_error_code(validator_setup["context"])
    assert (
        "Method must define a request message"
        in list_ctx_error_messages(validator_setup["context"])[0]
    )


def test_method_invalid_req_res(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[],
        service=validator_setup["service"],
        response=int,
        method=agen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    codes = list_ctx_error_code(validator_setup["context"])
    assert len(codes) == 2
    assert "E801" in codes
    assert "E805" in codes


def test_method_many_req(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[ValidClass, ValidClass2],
        service=validator_setup["service"],
        response=ValidClass,
        method=not_gen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert "E801" in list_ctx_error_code(validator_setup["context"])
    assert (
        "Only one request message allowed per method"
        in list_ctx_error_messages(validator_setup["context"])[0]
    )


def test_method_single_and_stream_req(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[AsyncIterator[ValidClass], ValidClass],
        service=validator_setup["service"],
        response=ValidClass2,
        method=not_gen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert "E801" in list_ctx_error_code(validator_setup["context"])
    assert (
        "Stream and Single request mixed in the args"
        in list_ctx_error_messages(validator_setup["context"])[0]
    )


def test_method_empty_res(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[AsyncIterator[ValidClass]],
        service=validator_setup["service"],
        response=None,
        method=not_gen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert "E804" in list_ctx_error_code(validator_setup["context"])
    assert (
        "Response type is 'None'"
        in list_ctx_error_messages(validator_setup["context"])[0]
    )


def test_method_invalid_res(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[AsyncIterator[ValidClass]],
        service=validator_setup["service"],
        response=Path,
        method=agen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert "E805" in list_ctx_error_code(validator_setup["context"])
    assert (
        "Invalid Streaming mode return type"
        in list_ctx_error_messages(validator_setup["context"])[0]
    )


def test_method_no_async_res(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[ValidClass],
        service=validator_setup["service"],
        response=AsyncIterator[ValidClass],
        method=not_async,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert "E805" in list_ctx_error_code(validator_setup["context"])


def test_method_no_gen_res(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "Method1",
        requests=[ValidClass],
        service=validator_setup["service"],
        response=AsyncIterator[ValidClass],
        method=not_gen,
    )
    validator_setup["validator"].execute(
        [validator_setup["service"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert "E805" in list_ctx_error_code(validator_setup["context"])
