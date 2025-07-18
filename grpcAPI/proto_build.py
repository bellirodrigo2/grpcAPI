from pathlib import Path

from makeproto import compile_service
from typing_extensions import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
)

from grpcAPI.app import APIService
from grpcAPI.files_sentinel import ensure_dirs, register_path
from grpcAPI.interfaces import ProcessService
from grpcAPI.makeproto_pass import validate_signature_pass


def pack_protos(
    services: Dict[str, List[APIService]],
    root_dir: Path,
    type_cast: Sequence[Tuple[Type[Any], Type[Any]]],
    process_services: Optional[List[ProcessService]] = None,
    out_dir: Optional[Path] = None,
    overwrite: bool = True,
    clean_services: bool = True,
) -> Set[str]:

    out_dir = out_dir or root_dir

    process_services = process_services or []

    for service_list in services.values():
        for service in service_list:
            for proc in process_services:
                proc(service)

    def compilepass(func: Callable[..., Any]) -> List[str]:
        return validate_signature_pass(func, type_cast)

    proto_stream = compile_service(
        services=services,
        custompassmethod=compilepass,
        version=3,
    )
    if not proto_stream:
        raise Exception("Service .proto file compilation failed")

    generated_files: Set[str] = set()
    for proto in proto_stream:
        file_path = f"{proto.filename}.proto"
        if proto.package:
            file_path = f"{proto.package}/{file_path}"
        write_proto(
            proto_str=proto.content,
            dst_dir=out_dir,
            file_path=file_path,
            overwrite=overwrite,
            clean=clean_services,
        )
        if clean_services:
            register_path(out_dir / file_path)
        generated_files.add(file_path)
    return generated_files


def write_proto(
    proto_str: str, dst_dir: Path, file_path: str, overwrite: bool, clean: bool
) -> None:
    abs_file_path = dst_dir / file_path
    ensure_dirs(abs_file_path.parent, clean)

    if abs_file_path.exists() and not overwrite:
        raise FileExistsError(f"{abs_file_path} already exists.")

    with open(abs_file_path, "w") as f:
        f.write(proto_str)
