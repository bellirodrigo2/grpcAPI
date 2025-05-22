from collections.abc import AsyncGenerator as ABCAsyncGenerator
from typing import Any

from typing_extensions import Annotated as typing_extensions_Annotated

try:
    from typing import Annotated as typing_Annotated
except ImportError:
    typing_Annotated = None


def is_Annotated(origin: type[Any]) -> bool:
    return origin in (typing_extensions_Annotated, typing_Annotated)


def is_asyncgen(origin: type[Any]) -> bool:
    return origin is ABCAsyncGenerator
