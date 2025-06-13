import unittest
from dataclasses import dataclass

from grpcAPI.ctxinject.inject import UnresolvedInjectableError, resolve
from grpcAPI.ctxinject.model import ArgsInjectable, DependsInject, ModelFieldInject


class User(str): ...


@dataclass
class Settings:
    debug: bool
    timeout: int


def sub_dep(
    uid: int = ArgsInjectable(...),
    timeout: int = ModelFieldInject(Settings, field="timeout"),
) -> str:
    return f"{uid}-{timeout}"


def mid_dep(
    name: User,
    uid: int = DependsInject(sub_dep),
    debug: bool = DependsInject(lambda debug: not debug),
) -> str:
    return f"{name}-{uid}-{debug}"


async def handler(
    name: User,
    id: int = ArgsInjectable(),
    to: int = ModelFieldInject(Settings, field="timeout"),
    combined: str = DependsInject(mid_dep),
    extra: str = DependsInject(lambda: "static"),
) -> str:
    return f"{name}|{id}|{to}|{combined}|{extra}"


class TestCombinedInject(unittest.IsolatedAsyncioTestCase):

    async def test_mixed_injectables(self) -> None:
        context = {
            "id": 42,
            "uid": 99,
            "debug": False,
            User: "Alice",
            Settings: Settings(debug=True, timeout=30),
        }
        result = await resolve(handler, context=context, overrides={})
        self.assertEqual(result, "Alice|42|30|Alice-99-False|static")

    async def test_mixed_injectables_missing_ctx(self) -> None:
        context = {
            "id": 42,
            "debug": False,
            User: "Alice",
            Settings: Settings(debug=True, timeout=30),
        }
        with self.assertRaises(UnresolvedInjectableError):
            await resolve(handler, context=context, overrides={})
