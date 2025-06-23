from pathlib import Path
from typing import Any, Dict

from grpcAPI.app import App
from grpcAPI.commands.utils import load_app
from grpcAPI.module_import import import_modules
from grpcAPI.server import Server
from grpcAPI.service_provider import make_service_classes


def compile_all(output_dir: Path, subfolder: str) -> None:
    compiled_dir = output_dir / subfolder
    compiled_dir.mkdir(parents=True, exist_ok=True)

    # compile com protoc
    # compilar para um temp ?


async def run_app(app_path: str, settings: Dict[str, Any]) -> None:

    load_app(app_path)

    src_dir = Path(settings.get("output_dir", "./grpcAPI/proto"))

    # compilar com protocz
    compile_all(src_dir, "compiled")
    modules = import_modules(src_dir, ["compiled"])

    server = Server(modules)

    app = App()
    services = await make_service_classes(app.packages, modules)

    for service in services:
        server.add_service(service)
    await server.start()
