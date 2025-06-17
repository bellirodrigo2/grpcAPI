import unittest
from typing import Annotated, Any, Callable, Dict

from grpcAPI.ctxinject.inject import inject_args
from grpcAPI.ctxinject.model import Depends
from grpcAPI.ctxinject.sigcheck import func_signature_check
from grpcAPI.proto_inject import FromContext, FromRequest
from grpcAPI.proxy import IteratorProxy, Proxy
from grpcAPI.types import Context, Stream


def getdb() -> str:
    return "sqlite"


class MyRequest(Proxy):
    name: str


async def handler1(
    req: MyRequest,
) -> str:
    return req.name


async def handler2(req: MyRequest, ctx: Context) -> str:
    return req.name + ctx.peer()


async def handler3(req: MyRequest, ctx: Context, db: str = Depends(getdb)) -> str:
    return req.name + ctx.peer() + db


async def handler4(
    req: Annotated[MyRequest, "request"],
    ctx: Context,
    db: Annotated[str, Depends(getdb)],
) -> str:
    return req.name + ctx.peer() + db


async def handler5(req: Stream[MyRequest], ctx: Context) -> str:
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


class InnerMyRequest:
    def __init__(self, name: str) -> None:
        self.name = name


class MyContext:
    def peer(self) -> str:
        return "foobar"


class TestValidateFunc(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:

        my_request = MyRequest(InnerMyRequest("foobar"))
        context = MyContext()

        injctx = {MyRequest: my_request, Context: context}

        async def inject(
            func: Callable[..., Any], inj_ctx: Dict[Any, Any] = injctx
        ) -> Any:
            errors = func_signature_check(func, [Proxy, Context], Stream)
            self.assertEqual(len(errors), 0)
            result_func = await inject_args(func, inj_ctx, False)
            result = await result_func()
            return result

        self.inject = inject

    async def test_inject1(self) -> None:

        result = await self.inject(handler1)
        self.assertEqual(result, "foobar")

    async def test_inject2(self) -> None:

        result = await self.inject(handler2)
        self.assertEqual(result, "foobarfoobar")

    async def test_inject3(self) -> None:

        result = await self.inject(handler3)
        self.assertEqual(result, "foobarfoobarsqlite")

    async def test_inject4(self) -> None:

        result = await self.inject(handler4)
        self.assertEqual(result, "foobarfoobarsqlite")

    async def test_inject5(self) -> None:

        class MyRequestIterator:
            names = ["foo", "bar"]
            curr = 0

            def __aiter__(self) -> "MyRequestIterator":
                return self

            async def __anext__(self) -> Any:
                if self.curr >= len(self.names):
                    self.curr = 0
                    raise StopAsyncIteration
                tgt = self.names[self.curr]
                self.curr += 1
                return tgt

        proxy_it = IteratorProxy(MyRequestIterator(), InnerMyRequest)
        ctx = {Stream[MyRequest]: proxy_it, Context: MyContext()}
        result = await self.inject(handler5, ctx)
        self.assertEqual(result, "foobar")

    async def test_inject6(self) -> None:
        result = await self.inject(handler6)
        self.assertEqual(result, "foobar")

    async def test_inject7(self) -> None:
        result = await self.inject(handler7)
        self.assertEqual(result, "foobar")

    async def test_inject8(self) -> None:
        result = await self.inject(handler8)
        self.assertEqual(result, "foobar")
