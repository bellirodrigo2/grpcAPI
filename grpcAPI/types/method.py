from collections.abc import AsyncIterator
from typing import Any, Optional, Tuple, Type, get_args, get_origin

Stream = AsyncIterator


def if_stream_get_type(bt: Type[Any]) -> Optional[type[Any]]:
    if get_origin(bt) is AsyncIterator:
        return get_args(bt)[0]
    return None


def get_func_arg_info(tgt: Type[Any]) -> Tuple[type[Any], bool]:
    argtype = if_stream_get_type(tgt)
    if argtype is not None:
        return argtype, True
    return tgt, False
