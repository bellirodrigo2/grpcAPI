from logging import Logger
from typing import Any, Optional

from grpcAPI.app import App
from grpcAPI.commands.command import GRPCAPICommand
from grpcAPI.proto_build import make_protos


def run_lint(app: App, logger: Logger) -> None:
    files = make_protos(app.services)
    logger.info("Protos have been successfully generated.")
    logger.debug("Generated files:", [(f.package, f.filename) for f in files])


class LintCommand(GRPCAPICommand):

    def __init__(
        self, app_path: str, settings_path: Optional[str] = None
    ) -> None:
        super().__init__('lint', app_path, settings_path)

    async def run(self, **kwargs: Any) -> None:
        run_lint(self.app, self.logger)
