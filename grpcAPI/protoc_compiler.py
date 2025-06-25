import argparse
import os
from pathlib import Path

from grpc_tools import protoc


def compile(tgt_folder: str, protofile: str, output_dir: str) -> bool:

    folder = Path(tgt_folder)
    filepath = folder / protofile

    if not os.path.exists(filepath):
        raise Exception(f"File {protofile} does not exists")

    os.makedirs(output_dir, exist_ok=True)
    init_file = Path(output_dir) / "__init__.py"
    if not init_file.exists():
        init_file.touch()
    result = protoc.main(
        [
            "grpc_tools.protoc",
            f"--proto_path={tgt_folder}",
            f"--python_out={output_dir}",
            f"--grpc_python_out={output_dir}",
            str(filepath),
        ]
    )
    if result == 0:
        return True
    else:
        raise Exception(f'Error compiling "{protofile}"')


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile .proto file to Python class")
    parser.add_argument("-file", "--protofile", help=".proto file name")
    parser.add_argument("-folder", "--folder", help=".proto file name")
    parser.add_argument(
        "-o", "--output_dir", help="Output Folder target for compiled files"
    )

    args = parser.parse_args()

    compile(args.folder, args.protofile, args.output_dir)


if __name__ == "__main__":
    main()
