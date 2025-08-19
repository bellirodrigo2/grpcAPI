from pathlib import Path

from grpcAPI.protoc.compile import compile_protoc


def main() -> None:

    prototypes_path = Path(__file__).parent
    root = prototypes_path / "proto"
    dst = prototypes_path / "lib"
    compile_protoc(
        root,
        dst,
        True,
        False,
        True,
    )


if __name__ == "__main__":
    main()
