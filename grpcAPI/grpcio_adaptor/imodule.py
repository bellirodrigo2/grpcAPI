from types import ModuleType

from typing_extensions import Any, Callable, Optional, Type

from grpcAPI.interface import IServiceModule


class GrpcioServiceModule(IServiceModule):

    def __init__(self, module: ModuleType) -> None:
        self.module = module

    def get_service_baseclass(self, service_name: str) -> Optional[Type[Any]]:
        return getattr(self.module, f"{service_name}Servicer", None)

    def get_add_server(self, service_name: str) -> Callable[..., Any]:
        return getattr(self.module, f"add_{service_name}Servicer_to_server")

    @classmethod
    def proto_to_pymodule(cls, name: str) -> str:
        module_name = name.replace(".proto", "_pb2_grpc.py")
        return module_name
