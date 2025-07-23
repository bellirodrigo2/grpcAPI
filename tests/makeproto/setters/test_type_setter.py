from collections.abc import AsyncIterator

import pytest

from grpcAPI.makeproto.compiler import CompilerContext
from grpcAPI.makeproto.setters.type import TypeSetter
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate
from tests.makeproto.test_helpers import make_method, make_service


class Mock1:
    package = "pack1"


class Nopack:
    package = ""


# ---------- Fixtures ----------


@pytest.fixture
def context() -> CompilerContext:
    return CompilerContext()


@pytest.fixture
def block() -> ServiceTemplate:
    return make_service("ValidBlock")


@pytest.fixture
def setter() -> TypeSetter:
    return TypeSetter()


# ---------- Testes ----------


def test_method_types_unary(
    block: ServiceTemplate, context: CompilerContext, setter: TypeSetter
) -> None:
    method: MethodTemplate = make_method(
        "Method1",
        requests=[Mock1],
        service=block,
        response=Mock1,
    )
    setter.execute([block], context)
    assert len(context) == 0
    assert method.request_str == "pack1.Mock1"
    assert method.request_stream is False
    assert method.response_str == "pack1.Mock1"
    assert method.response_stream is False


def test_method_types_client_stream(
    block: ServiceTemplate, context: CompilerContext, setter: TypeSetter
) -> None:
    method: MethodTemplate = make_method(
        "Method1",
        requests=[AsyncIterator[Mock1]],  # type: ignore
        service=block,
        response=Mock1,
    )
    setter.execute([block], context)
    assert len(context) == 0
    assert method.request_str == "pack1.Mock1"
    assert method.request_stream is True
    assert method.response_str == "pack1.Mock1"
    assert method.response_stream is False


def test_method_types_server_stream(
    block: ServiceTemplate, context: CompilerContext, setter: TypeSetter
) -> None:
    method: MethodTemplate = make_method(
        "Method1",
        requests=[Mock1],
        service=block,
        response=AsyncIterator[Mock1],  # type: ignore
    )
    setter.execute([block], context)
    assert len(context) == 0
    assert method.request_str == "pack1.Mock1"
    assert method.request_stream is False
    assert method.response_str == "pack1.Mock1"
    assert method.response_stream is True


def test_method_types_bidirectional_stream(
    block: ServiceTemplate, context: CompilerContext, setter: TypeSetter
) -> None:
    method: MethodTemplate = make_method(
        "Method1",
        requests=[AsyncIterator[Mock1]],  # type: ignore
        service=block,
        response=AsyncIterator[Mock1],  # type: ignore
    )
    setter.execute([block], context)
    assert len(context) == 0
    assert method.request_str == "pack1.Mock1"
    assert method.request_stream is True
    assert method.response_str == "pack1.Mock1"
    assert method.response_stream is True


def test_method_types_unary_no_package(
    block: ServiceTemplate, context: CompilerContext, setter: TypeSetter
) -> None:
    method: MethodTemplate = make_method(
        "Method1",
        requests=[Nopack],
        service=block,
        response=Nopack,
    )
    setter.execute([block], context)
    assert len(context) == 0
    assert method.request_str == "Nopack"
    assert method.request_stream is False
    assert method.response_str == "Nopack"
    assert method.response_stream is False


def test_method_same_package(context: CompilerContext, setter: TypeSetter) -> None:
    block = make_service("ValidBlock", package="pack1")
    method: MethodTemplate = make_method(
        "Method1",
        requests=[AsyncIterator[Mock1]],  # type: ignore
        service=block,
        response=AsyncIterator[Mock1],  # type: ignore
    )
    setter.execute([block], context)
    assert len(context) == 0
    assert method.request_str == "Mock1"
    assert method.request_stream is True
    assert method.response_str == "Mock1"
    assert method.response_stream is True


def test_method_types_unary_no_request(
    block: ServiceTemplate, context: CompilerContext, setter: TypeSetter
) -> None:
    make_method(
        "Method1",
        requests=[],
        service=block,
        response=Mock1,
    )
    setter.execute([block], context)
    assert len(context) == 1


def test_method_types_unary_no_response(
    block: ServiceTemplate, context: CompilerContext, setter: TypeSetter
) -> None:
    make_method(
        "Method1",
        requests=[Mock1],
        service=block,
        response=None,
    )
    setter.execute([block], context)
    assert len(context) == 1
