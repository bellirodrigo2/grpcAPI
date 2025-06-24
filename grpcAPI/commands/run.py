import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

import toml

from grpcAPI.app import App
from grpcAPI.commands.utils import load_app
from grpcAPI.ctxinject.validate import inject_validation
from grpcAPI.makeproto.protoc_compiler import compile
from grpcAPI.module_import import import_modules
from grpcAPI.persutil.versioning import get_current_version
from grpcAPI.server import IServer, Server
from grpcAPI.service_provider import make_service_classes


def list_proto_files(path: Path) -> list[Path]:
    return [p for p in path.iterdir() if str(p).endswith(".proto")]


def list_subfolders(path: Path) -> List[Path]:
    return [p for p in path.iterdir() if p.is_dir()]


@asynccontextmanager
async def compiler_lifespan(src_dir: Path, version: str) -> AsyncGenerator[Path, Any]:
    src_path = src_dir / version
    if not src_path.exists():
        raise ValueError(f'Can´t find version "{version}" on Source Path: "{src_path}"')

    packages = list_subfolders(src_path)
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        for package in packages:
            proto_files = list_proto_files(package)
            for file in proto_files:
                tgt_dir = output_dir / package.name
                tgt_dir.mkdir(exist_ok=True)

                compile(
                    tgt_folder=str(src_path),
                    protofile=f"{str(package.name)}/{str(file.name)}",
                    output_dir=str(output_dir),
                )
        yield output_dir


async def run_app(
    app_path: str,
    user_settings: Dict[str, Any],
    version: Optional[str],
    host: str,
    port: int,
    server: IServer = Server,
) -> None:

    std_settings: Dict[str, Any] = toml.load("./grpcAPI/commands/config.toml")
    std_settings = std_settings.get("run")

    if "run" in user_settings:
        user_settings = user_settings.get("run")
    settings = {**std_settings, **user_settings}

    load_app(app_path)

    src_dir = Path(settings.get("proto_dir", "./grpcAPI/proto"))

    if version is None:
        version = f"V{get_current_version(src_dir)}"

    version = version.upper()

    app = App()

    @asynccontextmanager
    async def lifespan(server: Server) -> AsyncGenerator[Any, Any]:
        async with compiler_lifespan(src_dir, version) as output_dir:
            modules = import_modules(output_dir.parent, [output_dir.name])
            server.modules = modules

            def inject_validation_wrapper(
                func: Callable[..., Any],
            ) -> Callable[..., Any]:
                inject_validation(func, app._caster)
                return func

            transform_func = inject_validation_wrapper
            overrides = app.dependency_overrides
            exception_registry = app._exception_handlers
            services = await make_service_classes(
                app.packages,
                modules,
                transform_func,
                overrides,
                exception_registry,
                app.error_log,
            )
            for service in services:
                server.add_service(service)

            if app.lifespan is None:
                yield
            else:
                async with app.lifespan(server):
                    yield

    block_wait = settings.get("block_wait", True)
    options = [
        (item["key"], item["value"]) for item in settings.get("server_options", [])
    ]
    health_check = settings.get("health_check", True)
    reflection = settings.get("reflection", True)

    server = server(
        modules={},
        block_wait=block_wait,
        options=options,
        health_check=health_check,
        reflection=reflection,
    )
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
