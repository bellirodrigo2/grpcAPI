import sys
from dataclasses import MISSING, Field, dataclass, fields, is_dataclass
from inspect import Parameter, signature
from typing import Any, Optional, TypeVar, Union, get_args, get_origin, get_type_hints

from typing_extensions import Annotated

T = TypeVar("T")


@dataclass  # (frozen=True)
class FuncArg:
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
        return False if self.getinstance(tgttype, default) is None else True


NO_DEFAULT = object()


def resolve_class_default(param: Parameter) -> tuple[bool, Any]:
    if param.default is not Parameter.empty:
        return True, param.default
    return False, NO_DEFAULT


def resolve_dataclass_default(field: Field[Any]) -> tuple[Any, ...]:

    if field.default is not MISSING:
        default = field.default
        has_default = True
    elif field.default_factory is not MISSING:
        default = field.default_factory  # armazena a fábrica, sem chamar
        has_default = True
    else:
        default = NO_DEFAULT
        has_default = False
    return has_default, default


def field_factory(
    obj: Union[Field[Any], Parameter],
    hint: Any,
    bt_default_fallback: bool = True,
) -> FuncArg:

    resolve_default = (
        resolve_class_default
        if isinstance(obj, Parameter)
        else resolve_dataclass_default
    )

    has_default, default = resolve_default(obj)

    argtype = hint

    if argtype is None and bt_default_fallback:
        argtype = type(default) if default not in (NO_DEFAULT, None) else None

    basetype = argtype
    extras = None

    if get_origin(hint) is Annotated:
        basetype, *extras_ = get_args(hint)
        extras = tuple(extras_)

    return FuncArg(
        name=obj.name,
        argtype=argtype,
        basetype=basetype,
        default=default,
        has_default=has_default,
        extras=extras,
    )


def map_class_fields(cls: type, bt_default_fallback: bool = True) -> list[FuncArg]:

    init_method = getattr(cls, "__init__", None)
    if is_dataclass(cls):
        return map_dataclass_fields(cls, bt_default_fallback)
    elif init_method and not isinstance(init_method, type(object.__init__)):
        return map_init_field(cls, bt_default_fallback)
    else:
        return map_model_fields(cls, bt_default_fallback)


def map_init_field(cls: type, bt_default_fallback: bool = True) -> list[FuncArg]:

    init_method = getattr(cls, "__init__", None)

    if init_method:
        hints = get_type_hints(
            init_method, globalns=vars(sys.modules[cls.__module__]), include_extras=True
        )
        sig = signature(init_method)
        items: list[tuple[str, Parameter]] = [
            (name, param) for name, param in sig.parameters.items() if name != "self"
        ]
        return [
            field_factory(obj, hints.get(name), bt_default_fallback)
            for name, obj in items
        ]
    raise ValueError("No __init__ defined for the class")


def map_dataclass_fields(cls: type, bt_default_fallback: bool = True) -> list[FuncArg]:

    hints = get_type_hints(
        cls, globalns=vars(sys.modules[cls.__module__]), include_extras=True
    )
    items = [(field.name, field) for field in fields(cls)]

    return [
        field_factory(obj, hints.get(name), bt_default_fallback) for name, obj in items
    ]


def map_model_fields(cls: type, bt_default_fallback: bool = True) -> list[FuncArg]:
    hints = get_type_hints(
        cls, globalns=vars(sys.modules[cls.__module__]), include_extras=True
    )
    items = [
        (
            name,
            Parameter(
                name,
                Parameter.POSITIONAL_OR_KEYWORD,
                default=getattr(cls, name, Parameter.empty),
            ),
        )
        for name, _ in hints.items()
    ]

    return [
        field_factory(obj, hints.get(name), bt_default_fallback) for name, obj in items
    ]
