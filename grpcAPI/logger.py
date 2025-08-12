__all__ = ["LOGGING_CONFIG", "logger_path"]
import logging
import logging.config
from pathlib import Path

import json5

logger_path = Path("./grpcAPI/commands/settings/config.json")
LOGGING_CONFIG = {}
with logger_path.open("r", encoding="utf-8") as f:
    config = json5.load(f)
    LOGGING_CONFIG = config.get("logger")
    logging.config.dictConfig(LOGGING_CONFIG)
