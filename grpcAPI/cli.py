import argparse
import asyncio
from typing import Tuple

from grpcAPI.commands.compile import compile_proto
from grpcAPI.commands.run import run_app
from grpcAPI.settings.utils import load_config


def get_args_compile(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> Tuple[argparse.ArgumentParser, str]:
    parser = subparsers.add_parser("compile", help="Compile the app to protofiles")
    parser.add_argument("app_path", help="Path to the app file")
    parser.add_argument(
        "--version",
        choices=["new", "overwrite", "draft", "lint"],
        default="new",
        help="Versioning mode: new (new version), overwrite (last version), draft, temporary or lint only.",
    )
    parser.add_argument("--config", help="Path to config file", default=None)
    return parser, "compile"


def get_args_run(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> Tuple[argparse.ArgumentParser, str]:
    parser = subparsers.add_parser("run", help="Run the gRPC app")
    parser.add_argument("app_path", help="Path to the app file")
    # parser.add_argument("--compile", action="store_true", help="Compile before running")
    parser.add_argument("--host", default=None, help="Host to bind")
    parser.add_argument("--version", default=None, help="Host to bind")
    parser.add_argument("--port", type=int, default=None, help="Port to bind")
    parser.add_argument("--config", help="Path to config file", default=None)
    return parser, "run"


def main() -> None:
    parser = argparse.ArgumentParser(prog="grpcapi")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser, compile_cmd = get_args_compile(subparsers)
    run_parser, run_cmd = get_args_run(subparsers)

    args = parser.parse_args()

    settings = load_config(getattr(args, "config", None), args.command)

    if args.command == compile_cmd:
        app_path = args.app_path
        version = args.version

        compile_proto(app_path, version, settings)

    elif args.command == run_cmd:
        app_path = args.app_path
        version = args.version
        host = args.host or settings.get("host", "127.0.0.1")
        port = args.port or settings.get("port", 50051)

        asyncio.run(
            run_app(
                app_path,
                settings,
                version,
                host,
                port,
            )
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
