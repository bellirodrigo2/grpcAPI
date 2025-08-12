import shutil
from pathlib import Path
from typing import Any, Optional

from grpcAPI.commands.command import BaseCommand


class InitCommand(BaseCommand):
    """Initialize grpcAPI configuration file in current directory."""

    def __init__(self, settings_path: Optional[str] = None) -> None:
        super().__init__('init', settings_path,True)
        
    def run_sync(self, **kwargs: Any) -> None:
        source_config = Path(__file__).parent / "settings" / "config.json"
        dst_folder = kwargs.get("dst_folder", Path.cwd())
        dest_config = Path(dst_folder) / "grpcapi.config.json"
        
        if dest_config.exists():
            overwrite = kwargs.get("force", False)
            if not overwrite:
                self.logger.warning(
                    f"""Configuration file already exists: {dest_config}
Use --force to overwrite existing file."""
                )
                return
        
        try:
            shutil.copy2(source_config, dest_config)
            
            self.logger.info(
                f"""Created grpcAPI configuration file: {dest_config.name}\n
                Edit this file to customize your grpcAPI settings."""
            )
            
            self.logger.info(
                f"""
                Next steps:
                   1. Edit {dest_config.name} to configure your project
                   2. Update proto_path, lib_path, and other settings as needed
                   3. Use comments (// or /* */) to document your configuration
                   4. Run grpcAPI commands from this directory to use your config"""
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create configuration file: {str(e)}")
            raise


def run_init(force: bool = False, dst_folder: Optional[Path] = None) -> None:
    """Standalone function to run init command."""
    try:
        init_command = InitCommand()
        kwargs = {"force": force}
        if dst_folder is not None:
            kwargs["dst_folder"] = dst_folder
        init_command.run_sync(**kwargs)
    except Exception as e:
        from logging import getLogger
        logger = getLogger(__name__)
        logger.error(f"Init failed: {str(e)}")
        raise