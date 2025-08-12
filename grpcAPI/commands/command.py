import asyncio
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Optional

from grpcAPI.app import GrpcAPI
from grpcAPI.commands.settings.utils import (
    combine_settings,
    load_app,
    load_file_by_extension,
)
from grpcAPI.process_service.run_process_service import run_process_service

default_logger = getLogger(__name__)


class GRPCAPICommand:
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
        self.command_name = command_name
        self.app_path = app_path
        self._is_sync = is_sync

        load_app(app_path)
        self.app = GrpcAPI()

        self.settings_path = settings_path

        if settings_path is not None:
            spath = Path(settings_path)
            user_settings = load_file_by_extension(spath)
        else:
            user_settings = {}
        self.settings = combine_settings(user_settings)
        run_process_service(self.app, self.settings)

        self.logger: Logger = default_logger

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
