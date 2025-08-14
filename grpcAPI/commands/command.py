import asyncio
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Dict, Optional

from grpcAPI.app import App, GrpcAPI
from grpcAPI.commands.settings.utils import (
    combine_settings,
    load_app,
    load_file_by_extension,
)
from grpcAPI.process_service.run_process_service import run_process_service

default_logger = getLogger(__name__)


def resolve_settings(settings_path: Optional[str]) -> Dict[str, Any]:
    if settings_path is not None:
        spath = Path(settings_path)
        user_settings = load_file_by_extension(spath)
    else:
        user_settings = {}
    return combine_settings(user_settings)


def resolve_app(app_path: str, settings: Dict[str, Any]) -> App:
    load_app(app_path)
    app = GrpcAPI()
    run_process_service(app, settings)
    return app


class BaseCommand:
    """
    Base class for gRPC API commands.
    """

    def __init__(
        self,
        command_name: str,
        settings_path: Optional[str] = None,
        is_sync: bool = False,
    ) -> None:
        self.command_name = command_name
        self._is_sync = is_sync
        self.settings_path = settings_path
        self.logger: Logger = default_logger

        self.settings = resolve_settings(settings_path)

    async def run(self, **kwargs: Any) -> Any:
        """Default async run method - override for async commands"""
        raise NotImplementedError("Subclasses must implement run method.")

    def run_sync(self, **kwargs: Any) -> Any:
        """Sync run method - override for sync commands"""
        # Default: run the async version
        return asyncio.run(self.run(**kwargs))

    def execute(self, **kwargs: Any) -> Any:
        """Universal executor that handles both sync and async commands"""
        if self._is_sync:
            return self.run_sync(**kwargs)
        else:
            return asyncio.run(self.run(**kwargs))


class GRPCAPICommand(BaseCommand):
    """
    Base class for gRPC API commands.
    """

    def __init__(
        self,
        command_name: str,
        app_path: str,
        settings_path: Optional[str] = None,
        is_sync: bool = False,
    ) -> None:
        super().__init__(command_name, settings_path, is_sync)
        self.app_path = app_path
        self.app = resolve_app(app_path, self.settings)
