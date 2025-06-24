import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Callable

from grpcAPI.ctxinject.validate import inject_validation
from grpcAPI.module_import import import_modules
from grpcAPI.server import Server
from grpcAPI.service_provider import make_service_classes
from tests.test_app_helper import make_app


async def serve() -> None:
    app = make_app()

    p = Path(__file__).parent / "proto"
    modules = import_modules(p, ["compiled"])

    server = Server(modules)

    def inject_validation_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
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

    @asynccontextmanager
    async def lifespan(server: Server) -> AsyncGenerator[None, None]:
        print("LIFESPAN: Starting server:", server)
        yield
        print("LIFESPAN: Shutting down server")

    for service in services:
        server.add_service(service)
    await server.start(lifespan=lifespan)


asyncio.run(serve())
