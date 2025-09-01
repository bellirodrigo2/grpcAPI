__all__ = ["LOGGING_CONFIG"]
import logging
import logging.config

import json5

from grpcAPI.commands.settings import DEFAULT_CONFIG_PATH

LOGGING_CONFIG = {}
with DEFAULT_CONFIG_PATH.open("r", encoding="utf-8") as f:
    config = json5.load(f)
    LOGGING_CONFIG = config.get("logger")
    logging.config.dictConfig(LOGGING_CONFIG)
