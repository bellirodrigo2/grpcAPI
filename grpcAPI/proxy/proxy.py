import enum
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    ItemsView,
    Iterator,
    KeysView,
    List,
    MutableMapping,
    MutableSequence,
    Union,
    ValuesView,
)


class ProxyMessage:

    def __init__(self, _wrapped: Any = None, **kwargs: Any):

        if isinstance(self, enum.Enum):
            return
        if _wrapped:
            self._wrapped = _wrapped
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
        if not isinstance(other, ProxyMessage):
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


class ListProxy(MutableSequence[Any]):
    def __init__(
        self,
        container: List[Any],
        get_v: Callable[[Any], Any],
        set_v: Callable[[Any], Any],
        base_type: type[Any],
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
        except TypeError:
            raise TypeError(
                f'At ListProxy set method for index: "{i}": Expected "{self._base_type.__name__}", found "{type(value).__name__}":{value}'
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
        except TypeError:
            raise TypeError(
                f'At ListProxy append method: Expected "{self._base_type.__name__}", found "{type(value).__name__}":{value}'
            )

    def extend(self, values: Any) -> None:
        try:
            self._container.extend(self._set_v(v) for v in values)
        except TypeError:
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


def EnumListProxy(container: List[Any], enum_type: type[enum.Enum]) -> ListProxy:
    return ListProxy(container, enum_type, lambda v: v.value, enum_type)


def MessageListProxy(container: List[Any], base_type: type[ProxyMessage]) -> ListProxy:
    return ListProxy(container, base_type, lambda v: v.unwrap, base_type)


def ValueListProxy(container: List[Any], base_type: type[Any]) -> ListProxy:
    return ListProxy(container, lambda v: v, lambda v: v, base_type)


DEFAULT_VALUE = object()


class DictProxy(MutableMapping[Any, Any]):
    def __init__(
        self,
        container: Dict[Any, Any],
        get_v: Callable[[Any], Any],
        set_v: Callable[[Any], Any],
        base_type: type[Any],
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

    def __setitem__(self, k: Any, v: Any) -> None:
        if v is None:
            raise TypeError(f'Can´t set "{k}" to None on DictProxy')
        try:
            if v is not None:
                self._container[k] = self._set_v(v)
        except (AttributeError, TypeError):
            raise TypeError(
                f'At DictProxy set method for key: "{k}": Expected "{self._base_type.__name__}", found "{type(v).__name__}":{v}'
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
            self._container[k] = self._set_v(v)

    def clear(self) -> None:
        self._container.clear()

    def __eq__(self, other: Any) -> bool:
        return dict(self.items()) == dict(other)

    def __len__(self) -> int:
        return len(self._container)

    def __repr__(self) -> str:
        return repr(dict(self.items()))


def EnumDictProxy(container: Dict[Any, Any], enum_type: type[enum.Enum]) -> DictProxy:
    return DictProxy(container, enum_type, lambda v: v.value, enum_type)


def MessageDictProxy(
    container: Dict[Any, Any], base_type: type[ProxyMessage]
) -> DictProxy:
    return DictProxy(container, base_type, lambda v: v.unwrap, base_type)


def ValueDictProxy(container: Dict[Any, Any], base_type: type[Any]) -> DictProxy:
    return DictProxy(container, lambda v: v, lambda v: v, base_type)
