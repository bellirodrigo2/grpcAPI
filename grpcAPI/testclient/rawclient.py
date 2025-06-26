import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, AsyncGenerator, Dict, Union

import grpc

from grpcAPI.proto_load import load_proto_temp_lifespan
from grpcAPI.proto_proxy import ProtoProxy, bind_proto_proxy


@asynccontextmanager
async def make_client_stubs(proto_path: Path) -> AsyncGenerator["ClientStubs", Any]:
    async with load_proto_temp_lifespan(proto_path) as modules:

        yield ClientStubs(modules=modules)


def get_service(
    modules: Dict[str, Dict[str, ModuleType]], package: str, module: str, service: str
) -> Any:
    pack_module = modules.get(package, None)
    if pack_module is None:
        raise KeyError(f'No package named "{package}"')

    grpc_module = f"{module}_grpc"
    proto_module = pack_module.get(grpc_module, None)
    if proto_module is None:
        raise KeyError(f'No module named "{grpc_module}" on package: "{package}"')

    service_stub_str = f"{service}Stub"
    service_stub = getattr(proto_module, service_stub_str, None)
    if service_stub is None:
        raise KeyError(f'No stub named "{service_stub_str}" on "{package}/{module}"')
    return service_stub


def run_method(request: Any, service: Any, method: str, host: str, port: int) -> Any:
    response = None
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = service(channel)
        method_func = getattr(stub, method)
        resp_obj = method_func(request.unwrap)
        response = resp_obj
    return response


@dataclass(frozen=True)
class ClientStubs:
    modules: Dict[str, Dict[str, ModuleType]]

    def get_service(
        self,
        package: str,
        module: str,
        service: str,
        host: str,
        port: int,
    ) -> "ClientService":

        service_stub = get_service(self.modules, package, module, service)
        return ClientService(host=host, port=port, service=service_stub)


@dataclass
class ClientService:
    host: str
    port: int
    service: Any

    def request(
        self,
        method: str,
        request: Any,
    ) -> Any:
        return run_method(request, self.service, method, self.host, self.port)


if __name__ == "__main__":

    class Proto1:
        @classmethod
        def protofile(cls) -> str:
            return "mod1"

        @classmethod
        def package(cls) -> Union[str, object]:
            return "pack1"

    class UserCode(Proto1, Enum):
        EMPLOYEE = 0
        SCHOOL = -247
        INACTIVE = 1

    class UserInput(Proto1, ProtoProxy):
        name: str
        code: UserCode
        age: int
        affilliation: str

    async def main() -> None:
        path = Path("./example/userpack/proto/V1")
        async with make_client_stubs(path) as stubs:
            user_service = stubs.get_service(
                "pack2", "mod2", "user_service", "localhost", 50051
            )

            bind_proto_proxy(UserInput, stubs.modules.get("pack1"))

            user_input = UserInput(
                name="rodrigo", code=UserCode.EMPLOYEE, age=99, affilliation="grpc"
            )
            response = user_service.request("newuser", user_input)
            print(response)

    asyncio.run(main())
