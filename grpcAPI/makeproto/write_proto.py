from pathlib import Path

from typing_extensions import Iterable, Set

from grpcAPI.makeproto import IProtoPackage
from grpcAPI.makeproto.files_sentinel import ensure_dirs, register_path


def write_protos(
    proto_stream: Iterable[IProtoPackage],
    out_dir: Path,
    overwrite: bool = True,
    clean_services: bool = True,
) -> Set[str]:
    generated_files: Set[str] = set()
    for proto in proto_stream:
        file_path = proto.qual_name
        abs_file_path = out_dir / file_path
        ensure_dirs(abs_file_path.parent, clean_services)
        created = write_proto(
            proto_str=proto.content,
            file_path=abs_file_path,
            overwrite=overwrite,
        )
        if created and clean_services:
            register_path(abs_file_path, False)
        generated_files.add(file_path)
    return generated_files


def write_proto(proto_str: str, file_path: Path, overwrite: bool) -> bool:
    file_existed = file_path.exists()
    if file_existed and not overwrite:
        raise FileExistsError(f"{file_path} already exists.")

    with open(file_path, "w") as f:
        f.write(proto_str)
    return not file_existed
