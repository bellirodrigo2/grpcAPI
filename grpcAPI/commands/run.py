import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, AsyncGenerator, Callable, Dict, List

from grpcAPI.app import App
from grpcAPI.commands.utils import load_app
from grpcAPI.ctxinject.validate import inject_validation
from grpcAPI.makeproto.protoc_compiler import compile
from grpcAPI.module_import import import_modules
from grpcAPI.server import Server
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


async def run_app(app_path: str, settings: Dict[str, Any], version: str) -> None:

    version = version.upper()

    load_app(app_path)

    src_dir = Path(settings.get("output_dir", "./grpcAPI/proto"))
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

    server = Server({})
    await server.start(lifespan=lifespan)


if __name__ == "__main__":

    asyncio.run(
        run_app(
            "./tests/test_app_helper.py",
            {"output_dir": "./example/userpack/proto"},
            "V1",
        )
    )
