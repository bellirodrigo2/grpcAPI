from datetime import datetime
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Type

import pytest
from typemapping import get_func_args
from typing_extensions import Annotated

from grpcAPI.data_types import AsyncContext, Depends, FromContext, FromRequest, Message
from grpcAPI.label_method import extract_request, extract_response
from grpcAPI.proto_build import validate_signature_pass
from grpcAPI.proto_ctxinject import convert_timestamp
from grpcAPI.protobut_typing import inject_proto_typing
from tests.conftest import (
    ClassMsg,
    InnerMessage,
    Other,
    Timestamp,
    User,
    UserCode,
)


def getdb() -> str:
    return "sqlite"


class MyRequest(Message):
    name: str


async def handler1(
    req: MyRequest,
) -> str:
    return req.name


async def handler2(req: MyRequest, ctx: AsyncContext) -> str:
    return req.name + ctx.peer()


async def handler3(req: MyRequest, ctx: AsyncContext, db: str = Depends(getdb)) -> str:
    return req.name + ctx.peer() + db


async def handler4(
    req: Annotated[MyRequest, "request"],
    ctx: AsyncContext,
    db: Annotated[str, Depends(getdb)],
) -> str:
    return req.name + ctx.peer() + db


async def handler5(req: AsyncIterator[MyRequest], ctx: AsyncContext) -> str:
    names = ""
    async for mr in req:
        names += mr.name
    return names


async def handler6(name: str = FromRequest(MyRequest)) -> str:
    return name


async def handler7(name: Annotated[str, FromRequest(MyRequest)]) -> str:
    return name


async def handler8(mydb: Annotated[str, FromRequest(MyRequest, "name")]) -> str:
    return mydb


async def handler9(
    mydb: Annotated[str, FromRequest(MyRequest, "name")], peer: str = FromContext()
) -> None:
    return


async def handler10(
    mydb: Annotated[str, FromRequest(MyRequest, "name")], peer: str = FromContext()
) -> MyRequest:
    pass


async def handler11(
    mydb: Annotated[str, FromRequest(MyRequest, "name")], peer: str = FromContext()
) -> AsyncIterator[MyRequest]:
    yield ""


# ERRORS


async def handler12(mydb: str, peer: str = FromContext()) -> AsyncIterator[MyRequest]:
    yield ""


async def handler13(mydb, arg2: str) -> MyRequest:
    yield ""


def run_tests(
    func: Callable[..., Any],
    expected_req: List[Type[Any]],
    expected_res: Optional[Type[Any]],
    validate_errors: int,
) -> None:
    assert extract_request(func) == expected_req
    if expected_res is None:
        assert extract_response(func) is None
    else:
        assert extract_response(func) == expected_res

    assert len(validate_signature_pass(func)) == validate_errors


def test_handler1() -> None:
    run_tests(handler1, [MyRequest], None, 0)


def test_handler2() -> None:
    run_tests(handler2, [MyRequest], None, 0)


def test_handler3() -> None:
    run_tests(handler3, [MyRequest], None, 0)


def test_handler4() -> None:
    run_tests(handler4, [MyRequest], None, 0)


def test_handler5() -> None:
    run_tests(handler5, [AsyncIterator[MyRequest]], None, 0)


def test_handler6() -> None:
    run_tests(handler6, [MyRequest], None, 0)


def test_handler7() -> None:
    run_tests(handler7, [MyRequest], None, 0)


def test_handler8() -> None:
    run_tests(handler8, [MyRequest], None, 0)


def test_handler9() -> None:
    run_tests(handler9, [MyRequest], None, 0)


def test_handler10() -> None:
    run_tests(handler10, [MyRequest], MyRequest, 0)


def test_handler11() -> None:
    run_tests(handler11, [MyRequest], AsyncIterator[MyRequest], 0)


def test_handler12() -> None:
    run_tests(handler12, [], AsyncIterator[MyRequest], 1)


def test_handler13() -> None:
    run_tests(handler13, [], MyRequest, 2)


def test_inject_typing() -> None:

    inject_proto_typing(User)

    async def get_db() -> str:
        return "sqlite"

    def func(
        other: Annotated[Other, FromRequest(User)],
        code: UserCode = FromRequest(User),
        age: InnerMessage = FromRequest(User),
        time: datetime = FromRequest(User),
        name: str = FromRequest(User),
        employee: str = FromRequest(User),
        inactive: bool = FromRequest(User),
        others: List[Other] = FromRequest(User),
        dict: Dict[str, str] = FromRequest(User),
        msg: ClassMsg = FromRequest(User),
        map_msg: Dict[int, InnerMessage] = FromRequest(User),
        code2: UserCode = FromRequest(User, field="code"),
        codes: List[UserCode] = FromRequest(User),
        map_codes: Dict[str, UserCode] = FromRequest(User),
        db: str = Depends(get_db),
    ) -> None:
        pass

    errors = validate_signature_pass(func)
    assert errors == []


def test_validate_date() -> None:

    def func(
        time: datetime = FromRequest(
            User, start=datetime(2023, 6, 6), end=datetime(2025, 6, 6)
        ),
    ) -> None:
        return

    args = get_func_args(func)
    modelinj = args[0].getinstance(FromRequest)

    modelinj._validator = convert_timestamp

    ts = Timestamp()
    ts.FromDatetime(datetime(2024, 6, 6))
    assert modelinj.validate(ts, basetype=datetime) == datetime(2024, 6, 6)

    with pytest.raises(ValueError):
        ts = Timestamp()
        ts.FromDatetime(datetime(2022, 6, 6))
        assert modelinj.validate(ts, basetype=datetime) == datetime(2024, 6, 6)

    with pytest.raises(ValueError):
        ts = Timestamp()
        ts.FromDatetime(datetime(2026, 6, 6))
        assert modelinj.validate(ts, basetype=datetime) == datetime(2024, 6, 6)
