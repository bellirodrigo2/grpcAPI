from types import ModuleType

from makeproto import ILabeledMethod, IMetaType
from typing_extensions import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    runtime_checkable,
)

from grpcAPI.exceptionhandler import ExceptionRegistry


class ExtractMetaType(Protocol):
    """"""

    def __call__(self, func: Callable[..., Any]) -> Tuple[
        List[IMetaType],
        Optional[IMetaType],
    ]: ...


class MethodSigValidation(Protocol):
    """"""

    def __call__(self, func: Callable[..., Any]) -> List[str]: ...


class MakeMethod(Protocol):
    """"""

    def __call__(
        self,
        labeledmethod: ILabeledMethod,
        overrides: Dict[Callable[..., Any], Callable[..., Any]],
        exception_registry: ExceptionRegistry,
    ) -> Callable[..., Any]: ...


@runtime_checkable
class IServiceModule(Protocol):
    """"""

    module: ModuleType

    def get_service_baseclass(self, service_name: str) -> Optional[Type[Any]]: ...

    def get_add_server(self, service_name: str) -> Callable[..., Any]: ...

    @classmethod
    def proto_to_pymodule(cls, name: str) -> str: ...
