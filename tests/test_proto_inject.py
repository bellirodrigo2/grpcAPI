import unittest
from typing import Annotated, get_args

from grpcAPI.app import ProtoModel
from grpcAPI.ctxinject.model import Depends
from grpcAPI.proto_inject import (
    FromContext,
    FromRequest,
    extract_request,
    validate_injectable_function,
)
from grpcAPI.types import Context, Stream


def getdb() -> str:
    return ""


class MyRequest(ProtoModel):
    name: str


async def handler1(
    req: MyRequest,
) -> None:
    return


async def handler2(req: MyRequest, ctx: Context) -> None:
    return


async def handler3(req: MyRequest, ctx: Context, db: str = Depends(getdb)) -> None:
    return


async def handler4(
    req: MyRequest, ctx: Context, db: Annotated[str, Depends(getdb)]
) -> None:
    return


async def handler5(req: Stream[MyRequest], ctx: Context) -> None:
    return


async def handler6(name: str = FromRequest(MyRequest)) -> None:
    return


async def handler7(name: Annotated[str, FromRequest(MyRequest)]) -> None:
    return


async def handler8(mydb: Annotated[str, FromRequest(MyRequest, "name")]) -> None:
    return


async def handler9(
    mydb: Annotated[str, FromRequest(MyRequest, "name")], peer: str = FromContext()
) -> None:
    return


class TestValidateFunc(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def test_validate_1(self) -> None:
        errors = validate_injectable_function(handler1)
        self.assertEqual(len(errors), 0)

    def test_validate_2(self) -> None:
        errors = validate_injectable_function(handler2)
        self.assertEqual(len(errors), 0)

    def test_validate_3(self) -> None:
        errors = validate_injectable_function(handler3)
        self.assertEqual(len(errors), 0)

    def test_validate_4(self) -> None:
        errors = validate_injectable_function(handler4)
        self.assertEqual(len(errors), 0)

    def test_validate_5(self) -> None:
        errors = validate_injectable_function(handler5)
        self.assertEqual(len(errors), 0)

    def test_validate_6(self) -> None:
        errors = validate_injectable_function(handler6)
        self.assertEqual(len(errors), 0)

    def test_validate_7(self) -> None:
        errors = validate_injectable_function(handler7)
        self.assertEqual(len(errors), 0)

    def test_validate_8(self) -> None:
        errors = validate_injectable_function(handler8)
        self.assertEqual(len(errors), 0)

    def test_validate_9(self) -> None:
        errors = validate_injectable_function(handler9)
        self.assertEqual(len(errors), 0)


class TestExtractRequest(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def test_validate_1(self) -> None:
        requests = extract_request(handler1)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(requests[0], ProtoModel))

    def test_validate_2(self) -> None:
        requests = extract_request(handler2)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(requests[0], ProtoModel))

    def test_validate_3(self) -> None:
        requests = extract_request(handler3)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(requests[0], ProtoModel))

    def test_validate_4(self) -> None:
        requests = extract_request(handler4)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(requests[0], ProtoModel))

    def test_validate_5(self) -> None:
        requests = extract_request(handler5)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(get_args(requests[0])[0], ProtoModel))

    def test_validate_6(self) -> None:
        requests = extract_request(handler6)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(requests[0], ProtoModel))

    def test_validate_7(self) -> None:
        requests = extract_request(handler7)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(requests[0], ProtoModel))

    def test_validate_8(self) -> None:
        requests = extract_request(handler8)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(requests[0], ProtoModel))

    def test_validate_9(self) -> None:
        requests = extract_request(handler9)
        self.assertEqual(len(requests), 1)
        self.assertTrue(issubclass(requests[0], ProtoModel))
