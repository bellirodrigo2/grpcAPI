"""
Pytest configuration for guber tests.

This file automatically loads fixtures for all tests in this directory.
"""

import logging
import warnings

# Suppress all SQLAlchemy warnings and logging
import sqlalchemy

from grpcAPI.commands.protoc import ProtocCommand

warnings.filterwarnings("ignore", category=sqlalchemy.exc.SAWarning)
warnings.filterwarnings(
    "ignore", message=".*garbage collector.*", category=sqlalchemy.exc.SAWarning
)
warnings.filterwarnings(
    "ignore", message=".*non-checked-in connection.*", category=sqlalchemy.exc.SAWarning
)
warnings.filterwarnings(
    "ignore", message=".*The garbage collector is trying to clean up.*"
)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="sqlalchemy")

# Disable SQLAlchemy logging completely for tests
logging.getLogger("sqlalchemy").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.orm").setLevel(logging.CRITICAL)

# Also suppress at the root level
sqlalchemy_logger = logging.getLogger("sqlalchemy")
sqlalchemy_logger.disabled = True

protoc = ProtocCommand()
protoc.execute(proto_path="example/guber/proto", lib_path="example/guber/lib")

from .fixtures import *  # noqa: F401, F403
