from typing_extensions import (
    Any,
    Callable,
    Iterable,
    Optional,
    Protocol,
    Sequence,
    Set,
    Type,
)


class IMetaType(Protocol):
    argtype: Type[Any]
    basetype: Type[Any]
    origin: Optional[Type[Any]]
    package: str
    proto_path: str


class ILabeledMethod(Protocol):
    name: str
    method: Callable[..., Any]
    package: str
    module: str
    service: str
    options: Sequence[str]
    comments: str
    request_types: Sequence[IMetaType]
    response_types: Optional[IMetaType]


class IService(Protocol):
    name: str
    module: str
    package: str
    options: Sequence[str]
    comments: str

    module_level_options: Iterable[str]
    module_level_comments: Iterable[str]

    @property
    def methods(self) -> Sequence[ILabeledMethod]: ...  # pragma: no cover

    @property
    def qual_name(self) -> str: ...  # pragma: no cover


class IProtoPackage(Protocol):
    package: str
    filename: str
    content: str
    depends: Set[str]

    @property
    def qual_name(self) -> str: ...  # pragma: no cover
