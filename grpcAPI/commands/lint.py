from logging import Logger
from typing import Any, Iterable, Optional

from grpcAPI.app import App
from grpcAPI.commands.command import GRPCAPICommand
from grpcAPI.makeproto.interface import IProtoPackage
from grpcAPI.proto_build import make_protos


def run_lint(app: App, logger: Logger) -> Iterable[IProtoPackage]:
    files = make_protos(app.services)
    file_list = list(files)
    logger.info("Protos have been successfully generated.")
    logger.debug("Generated files:", [(f.package, f.filename) for f in file_list])
    return file_list


class LintCommand(GRPCAPICommand):

    def __init__(self, app_path: str, settings_path: Optional[str] = None) -> None:
        super().__init__("lint", app_path, settings_path, is_sync=True)

    def run_sync(self, **kwargs: Any) -> Iterable[IProtoPackage]:
        return run_lint(self.app, self.logger)
