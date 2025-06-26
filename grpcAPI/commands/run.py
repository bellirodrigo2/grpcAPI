import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType
from typing import Any, AsyncGenerator, Callable, Dict, List, Type, Union

from grpcAPI.app import App
from grpcAPI.commands.utils import combine_settings, load_app
from grpcAPI.ctxinject.validate import inject_validation
from grpcAPI.persutil.versioning import get_current_version
from grpcAPI.proto_load import load_proto_temp_lifespan
from grpcAPI.server import IServer, Server
from grpcAPI.service_provider import make_service_classes


def load_services(
    app: App, modules: Dict[str, Dict[str, ModuleType]]
) -> List[Type[Any]]:
    def inject_validation_wrapper(
        func: Callable[..., Any],
    ) -> Callable[..., Any]:
        inject_validation(func, app._caster)
        return func

    transform_func = inject_validation_wrapper
    overrides = app.dependency_overrides
    exception_registry = app._exception_handlers
    return make_service_classes(
        app.packages,
        modules,
        transform_func,
        overrides,
        exception_registry,
        app.error_log,
    )


def define_path(settings: Dict[str, str], version: Union[str, int, None]) -> Path:

    src_dir = Path(settings.get("proto_dir", "./grpcAPI/proto"))

    if version is None:
        version = f"V{get_current_version(src_dir)}"
    if isinstance(version, int):
        version = f"V{version}"
    version = version.upper()
    src_path = src_dir / version
    if not src_path.exists():
        raise ValueError(f'Can´t find version "{version}" on Source Path: "{src_path}"')
    return src_path


def make_server(settings: Dict[str, Any]) -> IServer:

    block_wait = settings.get("block_wait", True)
    options = [
        (item["key"], item["value"]) for item in settings.get("server_options", [])
    ]
    health_check = settings.get("health_checking", True)
    reflection = settings.get("reflection", True)

    return Server(
        modules={},
        block_wait=block_wait,
        options=options,
        health_check=health_check,
        reflection=reflection,
    )


async def run_app(
    app_path: str,
    user_settings: Dict[str, Any],
    version: Union[str, int, None],
    host: str,
    port: int,
) -> None:

    settings = combine_settings(user_settings, "run")

    src_path = define_path(settings, version)

    load_app(app_path)
    app = App()

    @asynccontextmanager
    async def lifespan(server: Server) -> AsyncGenerator[Any, Any]:
        with load_proto_temp_lifespan(src_path) as modules:

            server.modules = modules

            services = load_services(app, modules)
            for service in services:
                server.add_service(service)

            if app.lifespan is None:
                yield
            else:
                async with app.lifespan(server):
                    yield

    server = make_server(settings)
    await server.start(host, port, lifespan=lifespan)


if __name__ == "__main__":

    asyncio.run(
        run_app(
            "./tests/test_app_helper.py",
            {"proto_dir": "./example/userpack/proto"},
            None,
            "0.0.0.0",
            50051,
        )
    )
