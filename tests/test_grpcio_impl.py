from typing import Annotated, Any, AsyncIterator, Callable, List, Optional, Type

from grpcAPI.grpcio_adaptor.extract_types import extract_request, extract_response
from grpcAPI.grpcio_adaptor.makeproto_pass import validate_signature_pass
from grpcAPI.types import BaseContext, Depends, FromContext, FromRequest, Message


def getdb() -> str:
    return "sqlite"


class MyRequest(Message):
    name: str


async def handler1(
    req: MyRequest,
) -> str:
    return req.name


async def handler2(req: MyRequest, ctx: BaseContext) -> str:
    return req.name + ctx.peer()


async def handler3(req: MyRequest, ctx: BaseContext, db: str = Depends(getdb)) -> str:
    return req.name + ctx.peer() + db


async def handler4(
    req: Annotated[MyRequest, "request"],
    ctx: BaseContext,
    db: Annotated[str, Depends(getdb)],
) -> str:
    return req.name + ctx.peer() + db


async def handler5(req: AsyncIterator[MyRequest], ctx: BaseContext) -> str:
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
