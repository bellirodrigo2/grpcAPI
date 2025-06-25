import enum
from copy import deepcopy
from enum import Enum
from functools import partial
from types import ModuleType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    get_args,
    get_origin,
)

from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.message import Message

from grpcAPI.proxy import DictProxy, ListProxy, Proxy, bind_proxy

Self = TypeVar("Self", bound="ProtoProxy")


class ProtoProxy(Proxy):

    def WhichOneof(self, oneof_group: str) -> Optional[str]:
        return self._wrapped.WhichOneof(oneof_group)

    def SerializeToString(self) -> bytes:
        return self._wrapped.SerializeToString()

    def ParseFromString(self: Self, data: bytes) -> Self:
        return self._wrapped.ParseFromString(data)

    def CopyFrom(self, other: Message) -> None:
        self._wrapped.CopyFrom(other)

    def MergeFrom(self, other: Message) -> None:
        self._wrapped.MergeFrom(other)

    def Clear(self) -> None:
        self._wrapped.Clear()

    def HasField(self, field_name: str) -> bool:
        return self._wrapped.HasField(field_name)

    def ClearField(self, field_name: str) -> None:
        self._wrapped.ClearField(field_name)

    def ListFields(self) -> List[tuple[FieldDescriptor, Any]]:
        return self._wrapped.ListFields()

    def IsInitialized(self) -> bool:
        return self._wrapped.IsInitialized()

    def ByteSize(self) -> int:
        return self._wrapped.ByteSize()

    def SetInParent(self) -> None:
        self._wrapped.SetInParent()

    def UnknownFields(self) -> Any:
        return self._wrapped.UnknownFields()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ProtoProxy):
            return False
        return self._wrapped == other._wrapped

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        return str(self._wrapped)

    def __repr__(self) -> str:
        return repr(self._wrapped)

    def __deepcopy__(self, memo: dict[int, Any]) -> "ProtoProxy":
        return self.__class__(_wrapped=deepcopy(self._wrapped, memo))


# ----------------- GETTERS -------------------------------------------------


def EnumListProxy(container: List[Any], enum_type: Type[enum.Enum]) -> ListProxy:
    return ListProxy(container, enum_type, lambda v: v.value, enum_type)


def MessageListProxy(container: List[Any], base_type: Type[Proxy]) -> ListProxy:
    return ListProxy(container, base_type, lambda v: v.unwrap, base_type)


def ValueListProxy(container: List[Any], base_type: Type[Any]) -> ListProxy:
    return ListProxy(container, lambda v: v, lambda v: v, base_type)


def list_getter_factory(bt: Type[Any], name: str) -> Callable[[Any], Any]:
    if issubclass(bt, Enum):
        return lambda self: EnumListProxy(getattr(self._wrapped, name), bt)
    elif issubclass(bt, ProtoProxy):
        return lambda self: MessageListProxy(getattr(self._wrapped, name), bt)
    else:
        return lambda self: ValueListProxy(getattr(self._wrapped, name), bt)


class DictProtoProxy(DictProxy):
    def _internal_setitem(self, k: Any, v: Any) -> None:
        self._container[k].CopyFrom(v.unwrap)


def EnumDictProxy(container: Dict[Any, Any], enum_type: Type[enum.Enum]) -> DictProxy:
    return DictProxy(container, enum_type, lambda v: v.value, enum_type)


def MessageDictProxy(container: Dict[Any, Any], base_type: Type[Proxy]) -> DictProxy:
    return DictProtoProxy(container, base_type, lambda v: v.unwrap, base_type)


def ValueDictProxy(container: Dict[Any, Any], base_type: Type[Any]) -> DictProxy:
    return DictProxy(container, lambda v: v, lambda v: v, base_type)


def dict_getter_factory(bt: Type[Any], name: str) -> Callable[[Any], Any]:
    if issubclass(bt, Enum):
        return lambda self: EnumDictProxy(getattr(self._wrapped, name), bt)
    elif issubclass(bt, ProtoProxy):
        return lambda self: MessageDictProxy(getattr(self._wrapped, name), bt)
    else:
        return lambda self: ValueDictProxy(getattr(self._wrapped, name), bt)


def single_getter_factory(bt: Type[Any], name: str) -> Callable[[Any], Any]:
    if issubclass(bt, Enum):
        return lambda self: bt(getattr(self._wrapped, name))
    elif issubclass(bt, ProtoProxy):
        return lambda self: bt(getattr(self._wrapped, name))
    else:
        return lambda self: getattr(self._wrapped, name)


def make_getter(name: str, bt: Type[Any]) -> Callable[[Any], Any]:
    origin = get_origin(bt)
    args = get_args(bt)

    if origin is list:
        bt = args[0]
        return list_getter_factory(bt, name)

    elif origin is dict:
        bt = args[1]
        return dict_getter_factory(bt, name)

    elif origin is None:
        return single_getter_factory(bt, name)
    raise TypeError(f'Can´t resolve getter for field: "{name}"')


# ----------------- SETTERS -------------------------------------------------


def list_setter_factory(bt: Type[Any], name: str) -> Callable[[Any, Any], Any]:

    def set_list(self: Any, value: Any, set_v: Callable[[Any], Any]) -> None:

        try:
            target = getattr(self._wrapped, name)
            target[:] = [set_v(v) for v in value]
        except (TypeError, AttributeError) as e:
            raise TypeError(
                f'At class "{self.__class__.__name__}", field: "{name}" set: Expected "List[{bt.__name__}]", found "{type(value).__name__}":{value}'
            ) from e

    def set_list_message(self: Any, value: Any) -> None:
        try:
            target = getattr(self.unwrap, name)
            del target[:]
            for item in value:
                msg = target.add()
                msg.CopyFrom(item.unwrap)
        except (TypeError, AttributeError) as e:
            raise TypeError(
                f'At class "{self.__class__.__name__}", field: "{name}" list[ProtoProxy] set failed: {value}'
            ) from e

    if issubclass(bt, Enum):
        return partial(set_list, set_v=lambda x: x.value)
    elif issubclass(bt, ProtoProxy):
        return set_list_message
    else:
        return partial(set_list, set_v=lambda x: x)


def dict_setter_factory(
    bt: Type[Any], dict_key: str, name: str
) -> Callable[[Any, Any], Any]:

    def set_dict(self: Any, value: dict[Any, Any], set_v: Callable[[Any], Any]) -> None:
        try:
            target = getattr(self._wrapped, name)
            target.clear()
            for k, v in value.items():
                target[k] = set_v(v)
        except (TypeError, AttributeError) as e:
            raise TypeError(
                f'At class "{self.__class__.__name__}", field: "{name}" set: Expected "dict[{dict_key},{bt.__name__}]", found "{type(value).__name__}": {value}'
            ) from e

    def set_dict_message(self: Any, value: Any) -> None:
        try:
            target = getattr(self.unwrap, name)
            target.clear()
            for k, v in value.items():
                target[k].CopyFrom(v.unwrap)
        except (TypeError, AttributeError) as e:
            raise TypeError(
                f'At class "{self.__class__.__name__}", field: "{name}" dict[ProtoProxy] set failed: {value}'
            ) from e

    if issubclass(bt, Enum):
        return partial(set_dict, set_v=lambda x: x.value)
    elif issubclass(bt, ProtoProxy):
        return set_dict_message
    else:
        return partial(set_dict, set_v=lambda x: x)


def single_setter_factory(bt: Type[Any], name: str) -> Callable[[Any, Any], Any]:
    def assign_value(self: ProtoProxy, value: Any, set_v: Callable[[Any], Any]) -> None:
        try:
            setattr(self.unwrap, name, set_v(value))
        except (TypeError, AttributeError) as e:
            raise TypeError(
                f'At class "{self.__class__.__name__}", field: "{name}" set: Expected "{bt.__name__}", found "{type(value).__name__}":{value}'
            ) from e

    def assign_message(self: ProtoProxy, value: Any) -> None:
        try:
            target = getattr(self.unwrap, name)
            target.CopyFrom(value.unwrap)
        except (TypeError, AttributeError) as e:
            raise TypeError(
                f'At class "{self.__class__.__name__}", field: "{name}" set: Expected "{bt.__name__}", found "{type(value).__name__}":{value}'
            ) from e

    if issubclass(bt, Enum):
        return partial(assign_value, set_v=lambda x: x.value)
    elif issubclass(bt, ProtoProxy):
        return assign_message
    else:
        return partial(assign_value, set_v=lambda x: x)


def make_setter(name: str, bt: Type[Any]) -> Callable[[Any, Any], Any]:
    origin = get_origin(bt)
    args = get_args(bt)

    if origin is list:
        bt = args[0]
        return list_setter_factory(bt, name)

    elif origin is dict:
        bt = args[1]
        return dict_setter_factory(bt, args[0].__name__, name)

    elif origin is None:
        return single_setter_factory(bt, name)
    raise TypeError(f'Can´t resolve setter for field: "{name}"')


# ----------------- KWARGS ------------------------------------------------


def single_kwarg_factory(bt: Type[Any]) -> Callable[[Any], Any]:
    if issubclass(bt, Enum):
        return lambda v: v.value
    elif issubclass(bt, ProtoProxy):
        return lambda v: v.unwrap
    else:
        return lambda v: v


def list_kwarg_factory(bt: Type[Any]) -> Callable[[Any], Any]:
    if issubclass(bt, Enum):
        return lambda value: [v.value for v in value]
    elif issubclass(bt, ProtoProxy):
        return lambda value: [v.unwrap for v in value]
    else:
        return lambda value: value


def dict_kwarg_factory(bt: Type[Any]) -> Callable[[Any], Any]:
    if issubclass(bt, Enum):
        return lambda value: {k: v.value for k, v in value.items()}
    elif issubclass(bt, ProtoProxy):
        return lambda value: {k: v.unwrap for k, v in value.items()}
    else:
        return lambda value: value


def make_kwarg(bt: Type[Any]) -> Callable[[Any], Any]:
    """
    Transform a dict of Python values (Message, Enum, list, dict)
    to viable args for protobuf constructor.
    """
    origin = get_origin(bt)
    args = get_args(bt)

    if origin is list:
        bt = args[0]
        return list_kwarg_factory(bt)

    elif origin is dict:
        bt = args[1]
        return dict_kwarg_factory(bt)

    elif origin is None:
        return single_kwarg_factory(bt)
    raise TypeError


def _get_class(
    mapcls: Type[Any],
    modules: Dict[str, ModuleType],
) -> type[Any]:

    def get(modname: str, clsname: str) -> Type[Any]:
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


def bind_proto_proxy(
    mapcls: Type[Any],
    modules: Dict[str, ModuleType],
) -> None:

    proto_cls = _get_class(mapcls, modules)

    bind_proxy(
        mapcls=mapcls,
        wrapped_class=proto_cls,
        make_getter=make_getter,
        make_setter=make_setter,
        make_kwarg=make_kwarg,
    )
