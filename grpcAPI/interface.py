from pathlib import Path
from types import ModuleType

from makeproto import ILabeledMethod
from typing_extensions import (
    Any,
    Callable,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    runtime_checkable,
)

type MakeLabeledMethod = Callable[
    [
        Callable[..., Any],
        str,
        str,
        str,
        str,
        str,
        str,
        List[str],
        List[str],
    ],
    ILabeledMethod,
]

type MethodSigValidation = Callable[[Any], List[str]]


@runtime_checkable
class IServiceModule(Protocol):
    module: ModuleType

    def get_service_baseclass(self, service_name: str) -> Optional[Type[Any]]: ...

    @classmethod
    def proto_to_pymodule(cls, name: str) -> str: ...
