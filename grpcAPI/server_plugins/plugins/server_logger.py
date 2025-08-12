import logging
import logging.config
from datetime import datetime
from logging import getLogger
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import grpc

from grpcAPI.logger import LOGGING_CONFIG
from grpcAPI.server import ServerPlugin, ServerWrapper
from grpcAPI.server_plugins import loader


def add_logger(name: str, **kwargs: Any) -> Tuple[str, List[str], bool]:
    loggers = LOGGING_CONFIG.get("loggers", {})
    if name in loggers:
        level = loggers[name].get("level", "DEBUG")
        handlers = loggers[name].get("handlers", ["console"])
        propagate = loggers[name].get("propagate", True)
        return level, handlers, propagate

    newlogger = loggers.get("grpcAPI", {}).copy()

    # level
    level = kwargs.get("level", newlogger.get("level", "DEBUG"))
    newlogger["level"] = level

    # file - FIX: access handlers from LOGGING_CONFIG, not from newlogger
    if "filename" in kwargs:
        handlers_config = LOGGING_CONFIG.get("handlers", {})
        new_handler = handlers_config.get("file", {}).copy()
        new_handler["filename"] = kwargs["filename"]

        # Ensure handlers exists in LOGGING_CONFIG
        if "handlers" not in LOGGING_CONFIG:
            LOGGING_CONFIG["handlers"] = {}

        LOGGING_CONFIG["handlers"]["server_logger_handler"] = new_handler

    # handlers
    handlers = set(newlogger.get("handlers", ["console"]))
    handlers.update([h.lower() for h in kwargs.get("handlers", [])])
    if "file" in handlers:
        handlers.remove("file")
        handlers.add("server_logger_handler")
    newlogger["handlers"] = list(handlers)

    # propagate
    if "propagate" in kwargs:
        newlogger["propagate"] = kwargs["propagate"]
    else:
        newlogger["propagate"] = True

    if "loggers" not in LOGGING_CONFIG:
        LOGGING_CONFIG["loggers"] = {}

    LOGGING_CONFIG["loggers"][name] = newlogger
    logging.config.dictConfig(LOGGING_CONFIG)
    return newlogger["level"], newlogger["handlers"], newlogger["propagate"]


class ServerLoggerPlugin(ServerPlugin):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        self._services: Dict[str, Iterable[str]] = {}
        self.level, self.handlers, self.propagate = add_logger(
            "server_logger_plugin", **kwargs  # FIX: consistent name
        )
        self._logger = getLogger("server_logger_plugin")  # FIX: consistent name
        self._server_starts: List[datetime] = []
        self._server_stops: List[datetime] = []
        self._wait_for_termination: bool = False

    @property
    def plugin_name(self) -> str:
        return "server_logger"

    @property
    def state(self) -> Mapping[str, Any]:
        return {
            "services": self._services,
            "logger": self._logger,
            "logger_config": {
                "level": self.level,
                "handlers": self.handlers,
                "propagate": self.propagate,
            },
        }

    def on_register(self, server: "ServerWrapper") -> None:
        # logger config details
        # server version, etc
        # migration_thread_pool: Optional[Executor] = None,
        # maximum_concurrent_rpcs: Optional[int] = None,
        # compression: Optional[grpc.Compression] = None,
        pass

    def on_add_service(
        self, service_name: str, methods_name: Iterable[str], server: "ServerWrapper"
    ) -> None:
        self._services[service_name] = methods_name
        self._logger.info(f"Service '{service_name}' added to server.")
        self._logger.debug(f"Methods: {list(methods_name)}")

    def on_add_port(
        self, address: str, credentials: Optional[grpc.ServerCredentials]
    ) -> None:
        security = "Secure" if credentials else "Insecure"
        self._logger.info(f"{security} port '{address}' added to server.")

    async def on_start(self, server: "ServerWrapper") -> None:
        self._server_starts.append(datetime.now())
        self._logger.info(
            f"Server started, {len(server.plugins)} plugins, {len(self._services)} services."
        )
        self._logger.debug(
            f"Server plugins: {[plugin.plugin_name for plugin in server.plugins]}"
        )
        services = ""
        for service, methods in self._services.items():
            services += f"{service}:\n {', '.join(methods)}\n"
        self._logger.debug(f"Registered services:\n{services}")

    async def on_wait_for_termination(self, timeout: Optional[float] = None) -> None:
        self._logger.info(f"Server is waiting for termination: timeout {timeout}.")
        self._wait_for_termination = True

    async def on_stop(self) -> None:
        self._server_stops.append(datetime.now())
        self._logger.info("Server stopped.")
        self._logger.debug(f"Waiting for termination: '{self._wait_for_termination}' ")
        self._logger.debug(
            f"Server last start {self._server_starts[-1]}. Runned for {self._server_stops[-1] - self._server_starts[-1]}."
        )
        self._wait_for_termination = False


def register() -> None:
    loader.register("server_logger", ServerLoggerPlugin)
