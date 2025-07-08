import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set

from makeproto import IService, compile_service

from grpcAPI.files_sentinel import ensure_dirs, register_path
from grpcAPI.interface import MethodSigValidation


def pack_protos(
    services: Dict[str, List[IService]],
    root_dir: Path,
    out_dir: Optional[Path] = None,
    custompassmethod: MethodSigValidation = lambda x: [],
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

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        generated_files: Set[str] = set()

        for proto in proto_stream:
            file_path = f"{proto.filename}.proto"
            if proto.package:
                file_path = f"{proto.package}/{file_path}"

            write_proto(
                proto_str=proto.content,
                dst_dir=tmp_dir,
                file_path=file_path,
                overwrite=overwrite,
                clean=False,  # no need to clean up temporary file
            )
            generated_files.add(file_path)

        ensure_dirs(out_dir, clean_services)
        copy_new_files(tmp_dir, out_dir, overwrite=overwrite)

        if clean_services:
            for rel_path in generated_files:
                register_path(out_dir / rel_path)

        return generated_files


def copy_new_files(
    src_dir: Path, dst_dir: Path, overwrite: bool = False, clean: bool = True
) -> None:
    """
    Recursively copy all files from src_dir to dst_dir, preserving structure.
    """
    for src_file in src_dir.rglob("*"):
        if not src_file.is_file():
            continue

        relative_path = src_file.relative_to(src_dir)
        dst_file = dst_dir / relative_path

        ensure_dirs(dst_file.parent, clean)

        if dst_file.exists() and not overwrite:
            raise FileExistsError(
                f"File {dst_file} already exists and overwrite is False"
            )

        shutil.copy2(src_file, dst_file)


def write_proto(
    proto_str: str, dst_dir: Path, file_path: str, overwrite: bool, clean: bool
) -> None:
    abs_file_path = dst_dir / file_path
    ensure_dirs(abs_file_path.parent, clean)

    if abs_file_path.exists() and not overwrite:
        raise FileExistsError(f"{abs_file_path} already exists.")

    with open(abs_file_path, "w") as f:
        f.write(proto_str)
