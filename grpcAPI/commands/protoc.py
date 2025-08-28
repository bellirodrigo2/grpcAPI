import sys
from pathlib import Path
from typing import Any, Optional

from grpcAPI.commands.command import BaseCommand
from grpcAPI.protoc.compile import compile_protoc


class ProtocCommand(BaseCommand):

    def __init__(self, settings_path: Optional[str] = None) -> None:
        super().__init__("protoc", settings_path, True)

    def run_sync(self, **kwargs: Any) -> Any:

        proto_path = kwargs.get("proto_path") or self.settings.get(
            "proto_path", "proto"
        )
        lib_path = kwargs.get("lib_path") or self.settings.get("lib_path", "lib")
        mypy_stubs = kwargs.get("mypy_stubs", True)

        try:
            proto_files = compile_protoc(
                root=Path(proto_path),
                dst=Path(lib_path),
                clss=True,
                services=False,
                mypy_stubs=mypy_stubs,
            )
            print(f"Successfully compiled proto files from {proto_path} to {lib_path}")
            return proto_files
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
