import re
from pathlib import Path
from typing import Any, Dict, Tuple


def get_host_port(
    settings: Dict[str, Any],
) -> Tuple[str, int]:
    host = settings.get("host", "localhost")
    port = settings.get("port", 50051)
    port = int(port)

    return host, port


def get_compile_proto_settings(
    settings: Dict[str, Any],
) -> Tuple[bool, bool]:
    compile_settings = settings.get("compile_proto", {})
    clean_services = compile_settings.get("clean_services", True)
    ovewrite = compile_settings.get("ovewrite", False)
    return clean_services, ovewrite


def get_proto_lib_path(
    settings: Dict[str, Any],
) -> Tuple[Path, Path]:

    root_path = Path("./").resolve()

    proto_str: str = settings.get("proto_path", "proto")
    proto_path = root_path / proto_str
    if not proto_path.exists():
        raise FileNotFoundError(str(proto_path))

    lib_str: str = settings.get("lib_path", "lib")
    lib_path = root_path / lib_str
    if not lib_path.exists():
        raise FileNotFoundError(str(lib_path))
    return proto_path, lib_path
