import inspect
import sys
from dataclasses import MISSING, Field, dataclass, fields, is_dataclass
from functools import partial
from inspect import Parameter, signature
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from typing_extensions import Annotated as typing_extensions_Annotated

from grpcAPI.types.message import BaseEnum, BaseMessage, get_BaseMessage

try:
    from typing import Annotated as typing_Annotated
except ImportError:
    typing_Annotated = None

T = TypeVar("T")


def is_Annotated(origin: type[Any]) -> bool:
    return origin in (typing_extensions_Annotated, typing_Annotated)


@dataclass
class VarTypeInfo:
    name: str
    argtype: Optional[type[Any]]
    basetype: Optional[type[Any]]
    default: Optional[Any]
    has_default: bool = False
    extras: Optional[tuple[Any]] = None

    @property
    def origin(self) -> Optional[type[Any]]:
        return get_origin(self.basetype)

    @property
    def args(self) -> tuple[Any, ...]:
        return get_args(self.basetype)

    def istype(self, tgttype: type) -> bool:
        try:
            return self.basetype == tgttype or (issubclass(self.basetype, tgttype))  # type: ignore
        except TypeError:
            return False

    def getinstance(self, tgttype: type[T], default: bool = True) -> Optional[T]:
        if self.extras is not None:
            founds = [e for e in self.extras if isinstance(e, tgttype)]
            if len(founds) > 0:
                return founds[0]
        if default and self.has_default and isinstance(self.default, tgttype):
            return self.default
        return None

    def hasinstance(self, tgttype: type, default: bool = True) -> bool:
        return self.getinstance(tgttype, default) is not None


class _NoDefault:
    def __repr__(self) -> str:
        return "NO_DEFAULT"

    def __str__(self) -> str:
        return "NO_DEFAULT"


NO_DEFAULT = _NoDefault()


def get_safe_type_hints(
    obj: Any, localns: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """
    Get type hints, including ForwardRef for Self
    """
    if inspect.isclass(obj):
        cls = obj
    elif inspect.isfunction(obj) or inspect.ismethod(obj):
        cls = obj.__qualname__.split(".")[0]
        cls = getattr(sys.modules[obj.__module__], cls, None)
    else:
        cls = None

    globalns = vars(sys.modules[obj.__module__]).copy()

    if cls and inspect.isclass(cls):
        globalns[cls.__name__] = cls
    return get_type_hints(obj, globalns=globalns, localns=localns, include_extras=True)


def resolve_class_default(param: Parameter) -> tuple[bool, Any]:
    if param.default is not Parameter.empty:
        return True, param.default
    return False, NO_DEFAULT


def resolve_dataclass_default(field: Field[Any]) -> tuple[bool, Any]:
    if field.default is not MISSING:
        return True, field.default
    elif field.default_factory is not MISSING:
        return True, field.default_factory
    return False, NO_DEFAULT


def field_factory(
    obj: Union[Field[Any], Parameter],
    hint: Any,
    bt_default_fallback: bool = True,
) -> VarTypeInfo:
    resolve_default = (
        resolve_class_default
        if isinstance(obj, Parameter)
        else resolve_dataclass_default
    )

    has_default, default = resolve_default(obj)
    if hint is not inspect._empty:
        argtype = hint
    elif bt_default_fallback:
        argtype = type(default) if default not in (NO_DEFAULT, None) else None
    else:
        argtype = None
    # daqui pra baixo
    funcarg = make_funcarg(
        name=obj.name,
        tgttype=argtype,
        annotation=hint,
        default=default,
        has_default=has_default,
    )
    return funcarg


def make_funcarg(
    name: str,
    tgttype: type[Any],
    annotation: Optional[type[Any]] = None,
    default: Any = None,
    has_default: bool = False,
) -> VarTypeInfo:

    basetype = tgttype
    extras = None

    if annotation is not None and is_Annotated(get_origin(annotation)):
        basetype, *extras_ = get_args(annotation)
        extras = tuple(extras_)
    return VarTypeInfo(
        name=name,
        argtype=tgttype,
        basetype=basetype,
        default=default,
        extras=extras,
        has_default=has_default,
    )


def map_class_fields(cls: type, bt_default_fallback: bool = True) -> list[VarTypeInfo]:
    init_method = getattr(cls, "__init__", None)
    if is_dataclass(cls):
        return map_dataclass_fields(cls, bt_default_fallback)
    elif init_method and not isinstance(init_method, type(object.__init__)):
        return map_init_field(cls, bt_default_fallback)
    else:
        return map_model_fields(cls, bt_default_fallback)


def map_init_field(
    cls: type,
    bt_default_fallback: bool = True,
    localns: Optional[dict[str, Any]] = None,
) -> list[VarTypeInfo]:
    init_method = getattr(cls, "__init__", None)
    if not init_method:
        raise ValueError("No __init__ defined for the class")
    hints = get_safe_type_hints(init_method, localns)
    sig = signature(init_method)
    items = [(name, param) for name, param in sig.parameters.items() if name != "self"]
    return [
        field_factory(obj, hints.get(name), bt_default_fallback) for name, obj in items
    ]


def map_dataclass_fields(
    cls: type,
    bt_default_fallback: bool = True,
    localns: Optional[dict[str, Any]] = None,
) -> list[VarTypeInfo]:
    hints = get_safe_type_hints(cls, localns)
    items = [(field.name, field) for field in fields(cls)]
    return [
        field_factory(obj, hints.get(name), bt_default_fallback) for name, obj in items
    ]


def map_model_fields(
    cls: type,
    bt_default_fallback: bool = True,
    localns: Optional[dict[str, Any]] = None,
) -> list[VarTypeInfo]:
    hints = get_safe_type_hints(cls, localns)
    items = [
        (
            name,
            Parameter(
                name,
                Parameter.POSITIONAL_OR_KEYWORD,
                default=getattr(cls, name, Parameter.empty),
            ),
        )
        for name in hints
    ]
    return [
        field_factory(obj, hints.get(name), bt_default_fallback) for name, obj in items
    ]


def map_return_type(
    func: Callable[..., Any], localns: Optional[dict[str, Any]] = None
) -> VarTypeInfo:
    sig = inspect.signature(func)
    hints = get_safe_type_hints(func, localns)
    raw_return_type = hints.get("return", sig.return_annotation)

    if raw_return_type is inspect.Signature.empty:
        raw_return_type = None

    return make_funcarg(
        name=func.__name__,
        tgttype=raw_return_type,
        annotation=raw_return_type,
    )


def map_func_args(
    func: Callable[..., Any], localns: Optional[dict[str, Any]] = None
) -> Tuple[Sequence[VarTypeInfo], VarTypeInfo]:
    partial_args = {}

    if isinstance(func, partial):
        partial_args = func.keywords or {}
        func = func.func

    sig = inspect.signature(func)
    hints = get_safe_type_hints(func, localns)

    funcargs: list[VarTypeInfo] = []

    for name, param in sig.parameters.items():
        if name in partial_args:
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        annotation: type = hints.get(name, param.annotation)
        arg = field_factory(param, annotation)
        funcargs.append(arg)
    return_type = map_return_type(func, localns)

    return funcargs, return_type


def get_func_args(
    func: Callable[..., Any], localns: Optional[dict[str, Any]] = None
) -> Sequence[VarTypeInfo]:
    funcargs, _ = map_func_args(func, localns)
    return funcargs


def cls_map(
    tgt: type[BaseMessage],
    visited: Optional[Set[type[BaseMessage]]] = None,
) -> Set[type[BaseMessage]]:

    if visited is None:
        visited = set()

    if tgt in visited:
        return visited

    if issubclass(tgt, BaseEnum) or issubclass(tgt, BaseMessage):
        visited.add(tgt)

        args = map_model_fields(tgt, False)

        for arg in args:
            if arg.istype(BaseMessage):
                msgs = cls_map(arg.basetype, visited)
                visited.update(msgs)
            elif arg.istype(BaseEnum):
                visited.add(arg.basetype)
    return visited


def map_service_classes(
    methods: List[Callable[..., Any]],
) -> Set[type[Union[BaseMessage, BaseEnum]]]:
    all_types: Set[type] = set()

    for method in methods:
        funcargs, return_type = map_func_args(method)

        for arg in funcargs:
            base = get_BaseMessage(arg.basetype)
            if base:
                all_types.add(base)
        base = get_BaseMessage(return_type.basetype)
        if base:
            all_types.add(base)
    classes: Set[type[Union[BaseMessage, BaseEnum]]] = set()
    for typ in all_types:
        clss = cls_map(typ)
        classes.update(clss)
    return classes
