import enum
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Generator,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Type,
    Union,
    ValuesView,
)

from typemapping import map_model_fields


class Proxy:

    def __init__(self, _wrapped: Any = None, **kwargs: Any):

        if isinstance(self, enum.Enum):
            return
        if _wrapped:
            # self._wrapped = _wrapped
            object.__setattr__(self, "_wrapped", _wrapped)
            return

        wrapped_class = getattr(self.__class__, "_wrapped_cls", None)
        if wrapped_class is None:
            raise TypeError(f'"_wrapped_cls" not set for "{self.__class__.__name__}"')

        build_wrapped_kwargs = getattr(self.__class__, "_wrapped_kwargs", None)
        if build_wrapped_kwargs is None:
            raise TypeError(
                f'"_wrapped_kwargs" not set for "{self.__class__.__name__}"'
            )

        wrapped_kwargs = build_wrapped_kwargs(kwargs)
        self._wrapped = wrapped_class(**wrapped_kwargs)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Proxy):
            return False
        return self._wrapped == other._wrapped

    @property
    def unwrap(self) -> Any:
        return self._wrapped

    def __repr__(self) -> str:
        fields = ", ".join(
            f"{k}={repr(getattr(self, k))}"
            for k in dir(self.__class__)
            if not k.startswith("_") and not callable(getattr(self.__class__, k))
        )
        return f"{self.__class__.__name__}({fields})"

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__slots__ or name == "_wrapped":
            super().__setattr__(name, value)
        else:
            setattr(self._wrapped, name, value)


class ListProxy(MutableSequence[Any]):
    def __init__(
        self,
        container: List[Any],
        get_v: Callable[[Any], Any],
        set_v: Callable[[Any], Any],
        base_type: Type[Any],
    ) -> None:
        self._container = container
        self._get_v = get_v
        self._set_v = set_v
        self._base_type = base_type

    def __getitem__(self, i: Any) -> Any:
        return self._get_v(self._container[i])

    def __setitem__(self, i: Any, value: Any) -> None:
        try:
            self._container[i] = self._set_v(value)
        except (TypeError, AttributeError):
            raise TypeError(
                f'At ListProxy setitem method for index: "{i}": Expected "{self._base_type.__name__}", found "{type(value).__name__}":{value}'
            )

    def __delitem__(self, index: Union[int, slice]) -> None:
        del self._container[index]

    def __iter__(self) -> Generator[Any, None, None]:
        return (self._get_v(v) for v in self._container)

    def __len__(self) -> int:
        return len(self._container)

    def __contains__(self, item: Any) -> bool:
        return any(self._get_v(v) == item for v in self._container)

    def append(self, value: Any) -> None:
        try:
            self._container.append(self._set_v(value))
        except (TypeError, AttributeError):
            raise TypeError(
                f'At ListProxy append method: Expected "{self._base_type.__name__}", found "{type(value).__name__}":{value}'
            )

    def extend(self, values: Any) -> None:
        try:
            self._container.extend(self._set_v(v) for v in values)
        except (TypeError, AttributeError):
            raise TypeError(
                f'At ListProxy extend method: Expected "List[{self._base_type.__name__}]", found "{type(values).__name__}":{values}'
            )

    def clear(self) -> None:
        del self._container[:]

    def insert(self, index: Any, value: Any) -> None:
        self._container.insert(index, self._set_v(value))

    def remove(self, value: Any) -> None:
        del self[self.index(value)]

    def pop(self, index: int = -1) -> Any:
        return self._get_v(self._container.pop(index))

    def index(self, value: Any, start: int = 0, stop: int = 9223372036854775807) -> int:
        for i in range(start, min(stop, len(self))):
            if self[i] == value:
                return i
        raise ValueError(f"{value!r} is not in list")

    def reverse(self) -> None:
        self._container.reverse()

    def sort(self) -> None:
        self._container.sort()

    def copy(self) -> List[Any]:
        return list(self)

    def __eq__(self, other: Any) -> bool:
        return list(self) == list(other)

    def __repr__(self) -> str:
        return repr(list(self))


DEFAULT_VALUE = object()


class DictProxy(MutableMapping[Any, Any]):
    def __init__(
        self,
        container: Dict[Any, Any],
        get_v: Callable[[Any], Any],
        set_v: Callable[[Any], Any],
        base_type: Type[Any],
    ):
        self._container = container
        self._get_v = get_v
        self._set_v = set_v
        self._base_type = base_type

    def __getitem__(self, k: Any) -> Any:
        value = self._container.get(k, DEFAULT_VALUE)
        if value is DEFAULT_VALUE:
            return None
        return self._get_v(value)

    def get(self, k: Any, default: Any = None) -> Any:
        value = self._container.get(k, DEFAULT_VALUE)
        if value is DEFAULT_VALUE:
            return default
        return self._get_v(value)

    def set(self, k: Any, v: Any) -> None:
        self[k] = v

    def _internal_setitem(self, k: Any, v: Any) -> None:
        self._container[k] = self._set_v(v)

    def __setitem__(self, k: Any, v: Any) -> None:
        if v is None:
            raise TypeError(f'Can´t set "{k}" to None on DictProxy')
        try:
            self._internal_setitem(k, v)
        except (AttributeError, TypeError):
            raise TypeError(
                f'At DictProxy setitem method for key: "{k}": Expected "{self._base_type.__name__}", found "{type(v).__name__}":{v}'
            )

    def __contains__(self, k: Any) -> bool:
        return k in self._container

    def __delitem__(self, k: Any) -> None:
        del self._container[k]

    def __iter__(self) -> Iterator[Any]:
        return iter(self._container)

    def keys(self) -> KeysView[Any]:
        return list(self._container.keys())

    def values(self) -> ValuesView[Any]:
        return [self._get_v(v) for v in self._container.values()]

    def items(self) -> ItemsView[Any, Any]:
        return [(k, self._get_v(v)) for k, v in self._container.items()]

    def update(self, d: Dict[Any, Any]) -> None:
        for k, v in d.items():
            self._internal_setitem(k, v)

    def clear(self) -> None:
        self._container.clear()

    def __eq__(self, other: Any) -> bool:
        return dict(self.items()) == dict(other)

    def __len__(self) -> int:
        return len(self._container)

    def __repr__(self) -> str:
        return repr(dict(self.items()))


def bind_proxy(
    mapcls: Type[Any],
    wrapped_class: Type[Any],
    make_getter: Callable[[str, Type[Any]], Callable[[Any], Any]],
    make_setter: Callable[[str, Type[Any]], Callable[[Any, Any], Any]],
    make_kwarg: Callable[[type[Any]], Any],
    tgtcls: Optional[type[Any]] = None,
) -> None:

    tgtcls = tgtcls or mapcls
    if "_wrapped_cls" in tgtcls.__dict__:
        return
    # if hasattr(tgtcls, "_wrapped_cls"):
    # return

    # bind wrapped class constructor
    tgtcls._wrapped_cls = wrapped_class

    fields = map_model_fields(mapcls)
    slot_names = tuple(f.name for f in fields)
    tgtcls.__slots__ = slot_names + ("_wrapped",)
    proto_kwargs: Dict[str, Callable[[Any], Any]] = {}

    for field in fields:
        name = field.name
        bt = field.basetype
        # set slots getter and setter
        getter = make_getter(name, bt)
        setter = make_setter(name, bt)
        setattr(tgtcls, field.name, property(getter, setter))

        try:
            proto_kwargs[field.name] = make_kwarg(bt)
        except TypeError:
            raise TypeError(
                f'Cannot resolve kwarg for class "{mapcls}", field "{field.name}"'
            )

    # set build proto kwargs
    def set_constructor(kwargs: Dict[str, Any]) -> Dict[str, Any]:
        constructor: Dict[str, Any] = {}
        for k, v in kwargs.items():
            if k not in proto_kwargs:
                raise TypeError(
                    f" {tgtcls.__name__}.__init__()  got an unexpected keyword argument '{k}'"
                )
            constructor[k] = proto_kwargs[k](v)
            # if k in proto_kwargs:
            # constructor[k] = proto_kwargs[k](v)
        return constructor

    tgtcls._wrapped_kwargs = set_constructor


class IteratorProxy:
    def __init__(
        self, aioreq_iter: Union[AsyncIterator, Iterable], proxy_cls: Type[Any]
    ) -> None:
        if hasattr(aioreq_iter, "__aiter__"):
            self._aiter = aioreq_iter
        else:
            self._aiter = self._wrap_sync_iter(aioreq_iter)

        self.proxy_cls = proxy_cls

    def __aiter__(self) -> "IteratorProxy":
        return self

    async def __anext__(self) -> Any:
        raw = await self._aiter.__anext__()
        return self.proxy_cls(raw)

    @staticmethod
    def _wrap_sync_iter(data: Iterable) -> AsyncIterator:
        class _AsyncIter:
            def __init__(self, it):
                self._it = iter(it)

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self._it)
                except StopIteration:
                    raise StopAsyncIteration

        return _AsyncIter(data)
