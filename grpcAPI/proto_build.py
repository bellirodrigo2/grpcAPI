from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Set

from makeproto import IService, compile_service

from grpcAPI.config import VALIDATE_SIGNATURE_PASS
from grpcAPI.files_sentinel import ensure_dirs, register_path
from grpcAPI.interface import MethodSigValidation


def pack_protos_(
    services: Dict[str, List[IService]],
    root_dir: Path,
    custompassmethod: MethodSigValidation,
    out_dir: Optional[Path] = None,
    overwrite: bool = True,
    clean_services: bool = True,
) -> Set[str]:

    out_dir = out_dir or root_dir

    proto_stream = compile_service(
        services=services,
        custompassmethod=custompassmethod,
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


pack_protos = partial(pack_protos_, custompassmethod=VALIDATE_SIGNATURE_PASS)
