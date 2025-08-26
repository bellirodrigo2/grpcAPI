from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Generator

import grpc

from grpcAPI.commands.settings.utils import load_file_by_extension
from grpcAPI.load_credential import get_client_certificate

GUBER_PATH = Path(__file__).parent.parent

guber_settings = load_file_by_extension(GUBER_PATH / "server/grpcapi.config.json")

SECURE = guber_settings.get("tls", {}).get("enabled", False)

CREDENTIAL_ROOT_PATH = str((GUBER_PATH / "certs/root.crt").resolve())
CREDENTIAL_ROOT = get_client_certificate(CREDENTIAL_ROOT_PATH)


@contextmanager
def get_channel(
    target: str = "localhost", port: str = "50051"
) -> Generator[grpc.Channel, Any, None]:

    target = f"{target}:{port}"
    if SECURE:
        with grpc.secure_channel(target, credentials=CREDENTIAL_ROOT) as channel:
            yield channel
    else:
        with grpc.insecure_channel(target) as channel:
            yield channel


@asynccontextmanager
async def get_async_channel(
    target: str = "localhost", port: str = "50051"
) -> AsyncGenerator[grpc.Channel, Any]:

    target = f"{target}:{port}"
    if SECURE:
        async with grpc.aio.secure_channel(
            target, credentials=CREDENTIAL_ROOT
        ) as channel:
            yield channel
    else:
        async with grpc.aio.insecure_channel(target) as channel:
            yield channel
