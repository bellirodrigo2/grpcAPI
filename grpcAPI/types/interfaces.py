from typing import Any, Callable, List, Protocol, Set, Union

from grpcAPI.types.message import BaseEnum, BaseMessage, ProtoOption, _NoPackage


class IMethod(Protocol):
    method: Callable[..., Any]
    description: str
    options: ProtoOption


class IService(Protocol):
    name: str
    module: str
    package: Union[str, _NoPackage]
    methods: List[IMethod]
    description: str
    options: ProtoOption


class IModule(Protocol):
    name: str
    package: Union[_NoPackage, str]
    description: str
    options: ProtoOption

    @property
    def services(self) -> List[IService]: ...

    @property
    def objects(self) -> Set[type[Union[BaseMessage, BaseEnum]]]: ...


class IPackage(Protocol):
    name: Union[_NoPackage, str]

    @property
    def modules(self) -> List[IModule]: ...
