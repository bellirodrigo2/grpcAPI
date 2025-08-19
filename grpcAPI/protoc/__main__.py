import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .compile import compile_protoc


def main() -> None:
    """Command-line interface for protoc compilation."""
    parser = argparse.ArgumentParser(
        description="Compile protocol buffer files using grpc_tools.protoc"
    )

    parser.add_argument(
        "proto", type=str, help="Proto directory containing .proto files"
    )

    parser.add_argument(
        "lib", type=str, help="Destination directory for compiled files"
    )

    parser.add_argument(
        "--no-classes",
        action="store_false",
        dest="clss",
        default=True,
        help="Skip generating Python classes (--python_out)",
    )

    parser.add_argument(
        "--services",
        action="store_true",
        default=False,
        help="Generate gRPC service stubs (--grpc_python_out)",
    )

    parser.add_argument(
        "--no-mypy-stubs",
        action="store_false",
        dest="mypy_stubs",
        default=True,
        help="Skip generating MyPy stubs (--mypy_out)",
    )

    parser.add_argument(
        "--files",
        nargs="*",
        type=str,
        default=None,
        help="Specific .proto files to compile (default: all .proto files in proto)",
    )

    args = parser.parse_args()

    proto_path = Path(args.proto)
    lib_path = Path(args.lib)

    files: Optional[List[str]] = args.files if args.files else None

    try:
        compile_protoc(
            root=proto_path,
            dst=lib_path,
            clss=args.clss,
            services=args.services,
            mypy_stubs=args.mypy_stubs,
            files=files,
        )
        print(f"Successfully compiled proto files from {proto_path} to {lib_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
