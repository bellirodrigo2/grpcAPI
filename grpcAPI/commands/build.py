import shutil
import tempfile
import zipfile
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Optional, Set

from grpcAPI.app import App
from grpcAPI.commands import GRPCAPICommand, lint
from grpcAPI.makeproto.write_proto import write_protos


def build_protos(
    app: App,
    logger: Logger,
    proto_path: Path,
    output_path: Path,
    overwrite: bool,
    zipcompress: bool,
) -> Set[str]:
    proto_files = lint.run_lint(app, logger)

    def _atomic_write(file_path: Path, overwrite: bool):
        if proto_path.exists():
            copy_proto_files(proto_path, file_path, logger)
        generated_files = write_protos(
            proto_stream=proto_files,
            out_dir=file_path,
            overwrite=overwrite,
            clean_services=False,
        )
        return generated_files

    if zipcompress:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            generated_files = _atomic_write(temp_path, True)
            zip_directory(temp_path, output_path / "protos.zip", logger)
            return generated_files
    else:
        return _atomic_write(output_path, overwrite)


def copy_proto_files(source_path: Path, dest_path: Path, logger: Logger) -> None:
    if not source_path.exists():
        logger.warning(f"Proto source path does not exist: {source_path}")
        return

    for proto_file in source_path.rglob("*.proto"):
        relative_path = proto_file.relative_to(source_path)
        dest_file = dest_path / relative_path

        # Create parent directories if they don't exist
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        shutil.copy2(proto_file, dest_file)
        logger.debug(f"Copied {proto_file} to {dest_file}")


def zip_directory(source_dir: Path, zip_path: Path, logger: Logger) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(source_dir)
                zipf.write(file_path, arcname)
                logger.debug(f"Added {file_path} to zip as {arcname}")

    logger.info(f"Created zip file: {zip_path}")


def get_proto_path(
    settings: Dict[str, Any],
) -> Path:

    root_path = Path("./").resolve()

    proto_str: str = settings.get("proto_path", "proto")
    proto_path = root_path / proto_str
    if not proto_path.exists():
        raise FileNotFoundError(str(proto_path))
    return proto_path


def get_lib_path(
    settings: Dict[str, Any],
) -> Path:

    root_path = Path("./").resolve()

    compile_settings = settings.get("compile_proto", {})
    lib_str: str = compile_settings.get("outdir", "./dist")
    lib_path = root_path / lib_str
    lib_path.mkdir(parents=True, exist_ok=True)
    return lib_path


class BuildCommand(GRPCAPICommand):

    def __init__(self, app: App, settings_path: Optional[str] = None) -> None:
        super().__init__("build", app, settings_path)

    async def run(self, **kwargs: Any) -> Set[str]:

        proto_path_raw = kwargs.get("proto_path") or get_proto_path(self.settings)
        outdir_raw = kwargs.get("outdir") or get_lib_path(self.settings)

        # Ensure paths are Path objects
        proto_path = (
            Path(proto_path_raw) if isinstance(proto_path_raw, str) else proto_path_raw
        )
        outdir = Path(outdir_raw) if isinstance(outdir_raw, str) else outdir_raw

        compile_settings = self.settings.get("compile_proto", {})
        overwrite = kwargs.get("overwrite") or compile_settings.get("overwrite", False)
        zipcompress = kwargs.get("zipcompress") or compile_settings.get(
            "zipcompress", False
        )

        return build_protos(
            app=self.app,
            logger=self.logger,
            proto_path=proto_path,
            output_path=outdir,
            overwrite=overwrite,
            zipcompress=zipcompress,
        )
