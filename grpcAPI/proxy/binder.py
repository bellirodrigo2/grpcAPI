from types import ModuleType
from typing import Any, Callable, Dict, Optional

from grpcAPI.mapclass import FuncArg, map_model_fields


def _get_class(
    mapcls: type[Any],
    modules: Dict[str, ModuleType],
) -> type[Any]:

    def get(modname: str, clsname: str) -> type[Any]:
        mod = modules.get(modname)
        if mod is None:
            raise KeyError(f'Module "{modname}" not found.')
        cls = getattr(mod, clsname, None)
        if cls is None:
            raise KeyError(f'Module "{modname}" has no class "{clsname}".')
        return cls

    protofile = getattr(mapcls, "protofile", None)
    if protofile is None:
        raise KeyError(f'Class "{mapcls.__name__}" has no protofile() set')
    return get(protofile(), mapcls.__name__)


def bind_proxy(
    mapcls: type[Any],
    modules: Dict[str, ModuleType],
    make_getter: Callable[[FuncArg], Callable[[Any], Any]],
    make_setter: Callable[[FuncArg], Callable[[Any, Any], Any]],
    make_kwarg: Callable[[FuncArg], Any],
    tgtcls: Optional[type[Any]] = None,
) -> None:

    tgtcls = tgtcls or mapcls
    if hasattr(tgtcls, "_wrapped_cls"):
        return

    # bind protobuf class constructor
    proto_cls = _get_class(mapcls, modules)
    tgtcls._wrapped_cls = proto_cls

    fields = map_model_fields(mapcls)
    slot_names = tuple(f.name for f in fields)
    tgtcls.__slots__ = slot_names + ("_wrapped",)

    proto_kwargs: Dict[str, Callable[[Any], Any]] = {}

    for field in fields:
        # set slots getter and setter
        getter = make_getter(field)
        setter = make_setter(field)
        setattr(tgtcls, field.name, property(getter, setter))

        try:
            proto_kwargs[field.name] = make_kwarg(field)
        except TypeError:
            raise TypeError(
                f'Cannot resolve kwarg for class "{mapcls}", field "{field.name}"'
            )

    # set build proto kwargs
    tgtcls._wrapped_kwargs = lambda kwargs: {  # type: ignore
        k: proto_kwargs[k](v) for k, v in kwargs.items()  # type: ignore
    }
