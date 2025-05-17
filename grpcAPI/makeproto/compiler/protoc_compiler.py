import argparse
import os
import subprocess
from pathlib import Path


def compile(
    tgt_folder: str, protofile: str, output_dir: str, compiler: str = "protoc"
) -> bool:

    folder = Path(tgt_folder)
    filepath = folder / protofile

    if not os.path.exists(filepath):
        raise Exception(f"File {protofile} does not exists")

    os.makedirs(output_dir, exist_ok=True)

    command = [
        compiler,
        f"--proto_path={tgt_folder}",
        f"--python_out={output_dir}",
        protofile,
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        return True
    else:
        raise Exception(f'Error when compiling file "{protofile}": {result.stderr}')


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile .proto file to Python class")
    parser.add_argument("-file", "--protofile", help=".proto file name")
    parser.add_argument("-folder", "--folder", help=".proto file name")
    parser.add_argument(
        "-o", "--output_dir", help="Output Folder target for compiled files"
    )
    parser.add_argument("-c", "--compiler", help="Choose compiler", default="protoc")

    args = parser.parse_args()

    compile(args.folder, args.protofile, args.output_dir, args.compiler)


if __name__ == "__main__":
    main()
