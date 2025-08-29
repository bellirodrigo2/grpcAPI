import asyncio
import os
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Dict, Optional

from grpcAPI.app import App
from grpcAPI.commands.settings.utils import combine_settings, load_file_by_extension
from grpcAPI.process_service.run_process_service import run_process_service

default_logger = getLogger(__name__)


def resolve_settings(settings_path: Optional[str]) -> Dict[str, Any]:
    if settings_path is not None:
        spath = Path(settings_path)
        user_settings = load_file_by_extension(spath)
    else:
        user_settings = {}
    return combine_settings(user_settings)


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

        app_environ = self.settings.get("app_environ", {})
        for key, value in app_environ.items():
            os.environ[key] = value

    async def run(self, **kwargs: Any) -> Any:
        raise NotImplementedError("Subclasses must implement run method.")

    def run_sync(self, **kwargs: Any) -> Any:
        return asyncio.run(self.run(**kwargs))

    def execute(self, **kwargs: Any) -> Any:
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
        app: App,
        settings_path: Optional[str] = None,
        is_sync: bool = False,
    ) -> None:
        super().__init__(command_name, settings_path, is_sync)
        self.app = app
        run_process_service(app, self.settings)
