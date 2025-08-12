import shutil
import tempfile
import zipfile
from logging import Logger
from pathlib import Path
from typing import Any, Optional, Set

from grpcAPI.app import App
from grpcAPI.commands import GRPCAPICommand, lint
from grpcAPI.makeproto.write_proto import write_protos


def build_protos(
    app: App,
    logger: Logger,
    proto_path: Path,
    output_path: Path,
    overwrite: bool,
    clean_services: bool,
    zipcompress: bool,
) -> Set[str]:
    proto_files = lint.run_lint(app, logger)

    if zipcompress:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            generated_files = write_protos(
                proto_stream=proto_files,
                out_dir=temp_path,
                overwrite=True,
                clean_services=clean_services,
            )

            if proto_path.exists():
                copy_proto_files(proto_path, temp_path, logger)

            zip_directory(temp_path, output_path / "protos.zip", logger)
            return generated_files
    else:
        generated_files = write_protos(
            proto_stream=proto_files,
            out_dir=output_path,
            overwrite=overwrite,
            clean_services=clean_services,
        )

        if proto_path.exists():
            copy_proto_files(proto_path, output_path, logger)

        return generated_files


def copy_proto_files(source_path: Path, dest_path: Path, logger: Logger) -> None:
    """Copy existing .proto files from source to destination, preserving directory structure"""
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
    """Zip all files in source directory to zip_path"""
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(source_dir)
                zipf.write(file_path, arcname)
                logger.debug(f"Added {file_path} to zip as {arcname}")

    logger.info(f"Created zip file: {zip_path}")


class BuildCommand(GRPCAPICommand):

    def __init__(self, app_path: str, settings_path: Optional[str] = None) -> None:
        super().__init__("build", app_path, settings_path)

    async def run(self, **kwargs: Any) -> None:
        from grpcAPI.commands.utils import (
            get_compile_proto_settings,
            get_proto_lib_path,
        )

        proto_path, output_path = get_proto_lib_path(self.settings)
        clean_services, overwrite = get_compile_proto_settings(self.settings)
        zipcompress = kwargs.get("zipcompress", False)

        build_protos(
            app=self.app,
            logger=self.logger,
            proto_path=proto_path,
            output_path=output_path,
            overwrite=overwrite,
            clean_services=clean_services,
            zipcompress=zipcompress,
        )
