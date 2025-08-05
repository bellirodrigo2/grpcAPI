from logging import getLogger
from pathlib import Path
from typing import Any, Optional

from grpcAPI.app import App
from grpcAPI.commands.process_service.run_process_service import run_process_service
from grpcAPI.commands.settings.utils import (
    combine_settings,
    load_app,
    load_file_by_extension,
)
from grpcAPI.logger import getLogger

default_logger = getLogger(__name__)


class GRPCAPICommand:
    """
    Base class for gRPC API commands.
    """

    def __init__(
        self, command_name: str, app_path: str, settings_path: Optional[str] = None
    ) -> None:
        self.command_name = command_name
        self.app_path = app_path

        load_app(app_path)
        self.app = App()

        self.settings_path = settings_path

        if settings_path is not None:
            spath = Path(settings_path)
            user_settings = load_file_by_extension(spath)
        else:
            user_settings = {}
        self.settings = combine_settings(user_settings)

        run_process_service(self.app, self.settings)

        self.logger = default_logger

    async def run(self, **kwargs: Any) -> None:
        raise NotImplementedError("Subclasses must implement the run method.")
