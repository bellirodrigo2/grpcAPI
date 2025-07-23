from typing import Any, Dict

import pytest

from grpcAPI.makeproto.compiler import CompilerContext, list_ctx_error_code
from grpcAPI.makeproto.validators.imports import ImportsValidator
from tests.makeproto.test_helpers import make_method, make_service


class ValidClass:
    proto_path = "path.proto"


class InvalidClass:
    pass


@pytest.fixture
def validator_setup() -> Dict[str, Any]:
    return {
        "validator": ImportsValidator(),
        "context": CompilerContext(),
        "block": make_service("ValidBlock"),
    }


def test_imports_ok(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "field1",
        service=validator_setup["block"],
        requests=[ValidClass],
        response=ValidClass,
    )
    validator_setup["validator"].execute(
        [validator_setup["block"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 0


def test_imports_invalid_request(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "field1",
        service=validator_setup["block"],
        requests=[InvalidClass],
        response=ValidClass,
    )
    validator_setup["validator"].execute(
        [validator_setup["block"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert all(
        code == "E201" for code in list_ctx_error_code(validator_setup["context"])
    )


def test_imports_invalid_response(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "field1",
        service=validator_setup["block"],
        requests=[ValidClass],
        response=InvalidClass,
    )
    validator_setup["validator"].execute(
        [validator_setup["block"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 1
    assert all(
        code == "E201" for code in list_ctx_error_code(validator_setup["context"])
    )


def test_imports_invalid_request_response(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "field1",
        service=validator_setup["block"],
        requests=[InvalidClass],
        response=InvalidClass,
    )
    validator_setup["validator"].execute(
        [validator_setup["block"]], validator_setup["context"]
    )
    assert len(validator_setup["context"]) == 2
    assert all(
        code == "E201" for code in list_ctx_error_code(validator_setup["context"])
    )


def test_imports_no_request(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "field1",
        service=validator_setup["block"],
        requests=[],
        response=ValidClass,
    )
    validator_setup["validator"].execute(
        [validator_setup["block"]], validator_setup["context"]
    )
    # no error here. should raise on type validator
    assert len(validator_setup["context"]) == 0


def test_imports_no_response(validator_setup: Dict[str, Any]) -> None:
    make_method(
        "field1",
        service=validator_setup["block"],
        requests=[ValidClass],
        response=None,
    )
    validator_setup["validator"].execute(
        [validator_setup["block"]], validator_setup["context"]
    )
    # no error here. should raise on type validator
    assert len(validator_setup["context"]) == 0
