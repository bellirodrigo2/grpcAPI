from typing import Any, Callable, List

from grpcAPI.makeproto.compiler import CompilerContext
from grpcAPI.makeproto.validators.custommethod import CustomPass
from tests.makeproto.test_helpers import make_method, make_service


def custommethod(_: Callable[..., Any]) -> List[str]:
    return ["test"]


def other_method(_: str) -> None:
    return None


def test_field_no_type() -> None:
    validator = CustomPass(
        visitmethod=custommethod,
        setdefault=other_method,
        reset=other_method,
        finish=other_method,
    )
    context = CompilerContext()
    block = make_service("ValidBlock")
    validator.execute([block], context)
    assert len(context) == 0

    make_method(
        "field1",
        service=block,
    )
    validator.execute([block], context)
    assert len(context) == 1
