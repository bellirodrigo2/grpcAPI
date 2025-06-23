import asyncio
from pathlib import Path

from grpcAPI.module_import import import_modules
from grpcAPI.server import Server
from grpcAPI.service_provider import make_service_classes
from tests.test_app_helper import make_app


async def serve() -> None:
    app = make_app()

    p = Path(__file__).parent / "proto"
    modules = import_modules(p, ["compiled"])

    server = Server(modules)

    services = await make_service_classes(app.packages, modules)

    for service in services:
        server.add_service(service)
    await server.start()


asyncio.run(serve())
