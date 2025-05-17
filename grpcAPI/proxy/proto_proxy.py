from types import ModuleType
from typing import Any, Dict

from grpcAPI.proxy.binder import bind_proxy
from grpcAPI.proxy.proto_get_set import make_getter, make_kwarg, make_setter


def bind_proto_proxy(
    mapcls: type[Any],
    modules: Dict[str, ModuleType],
) -> None:
    bind_proxy(
        mapcls=mapcls,
        modules=modules,
        make_getter=make_getter,
        make_setter=make_setter,
        make_kwarg=make_kwarg,
    )
