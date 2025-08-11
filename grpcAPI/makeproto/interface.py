from typing import List

from typing_extensions import Any, Callable, Iterable, Optional, Protocol, Set, Type


class IMetaType(Protocol):
    argtype: Type[Any]
    basetype: Type[Any]
    origin: Optional[Type[Any]]
    package: str
    proto_path: str


class IFilter(Protocol):
    package: str
    module: str
    tags: Iterable[str]
    active: bool


class ILabeledMethod(IFilter):
    name: str
    method: Callable[..., Any]
    service: str
    options: Iterable[str]
    comments: str
    request_types: Iterable[IMetaType]
    response_types: Optional[IMetaType]


class IService(IFilter):
    name: str
    options: Iterable[str]
    comments: str

    module_level_options: List[str]
    module_level_comments: List[str]

    @property
    def methods(self) -> Iterable[ILabeledMethod]: ...  # pragma: no cover

    @property
    def qual_name(self) -> str: ...  # pragma: no cover


class IProtoPackage(Protocol):
    package: str
    filename: str
    content: str
    depends: Set[str]

    @property
    def qual_name(self) -> str: ...  # pragma: no cover
