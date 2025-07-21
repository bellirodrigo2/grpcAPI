import json
import logging
import logging.config
from pathlib import Path

logger_path = Path("./grpcAPI/settings/config.json")
with logger_path.open("r", encoding="utf-8") as f:
    config = json.load(f)
    LOGGING_CONFIG = config.get("logger")
    logging.config.dictConfig(LOGGING_CONFIG)
logging.getLogger().setLevel(logging.ERROR)
