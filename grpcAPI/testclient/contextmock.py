import time
from typing import Iterable, Mapping, NoReturn

import grpc
from typing_extensions import Any, Callable, Optional, Sequence, Tuple

from grpcAPI.data_types import AsyncContext
from grpcAPI.testclient.tracker import Tracker

std_auth_context = {
    "x509_common_name": [b"default-client"],
    "transport_security_type": [b"ssl"],
}


class ContextMock:
    def __init__(self, *, peer: str = "127.0.0.1:12345", deadline: float = 60.0):
        self.tracker = Tracker(AsyncContext)

        self._peer = peer
        self._deadline = deadline
        self._start_time = time.monotonic()

        self._trailing_metadata = []
        self._code = ""
        self._details = ""
        self._cancelled = False
        self._done = False

        self._peer_identities = None
        self._peer_identity_key = None
        self._auth_context = {}

        self._callbacks = []

    # async methods
    async def read(self) -> Any:
        return self.tracker.read()

    async def write(self, message: Any) -> None:
        self.tracker.write(message)

    async def send_initial_metadata(
        self, initial_metadata: Sequence[Tuple[str, str]]
    ) -> None:
        self.tracker.send_initial_metadata(initial_metadata)

    async def abort(
        self,
        code: grpc.StatusCode,
        details: str = "",
        trailing_metadata: Sequence[Tuple[str, str]] = tuple(),
    ) -> NoReturn:
        self.tracker.abort(code, details, trailing_metadata)
        raise RuntimeError(f"gRPC aborted: {code} - {details}")

    # sync methods
    def set_trailing_metadata(
        self, trailing_metadata: Sequence[Tuple[str, str]]
    ) -> None:
        self.tracker.set_trailing_metadata(trailing_metadata)
        self._trailing_metadata = trailing_metadata

    def invocation_metadata(self) -> Optional[Sequence[Tuple[str, str]]]:
        self.tracker.invocation_metadata()
        return self._trailing_metadata

    def set_code(self, code: grpc.StatusCode) -> None:
        self.tracker.set_code(code)
        self._code = code

    def set_details(self, details: str) -> None:
        self.tracker.set_details(details)
        self._details = details

    def set_compression(self, compression: grpc.Compression) -> None:
        self.tracker.set_compression(compression)

    def disable_next_message_compression(self) -> None:
        self.tracker.disable_next_message_compression()

    def peer(self) -> str:
        self.tracker.peer()
        return self._peer

    def peer_identities(self) -> Optional[Iterable[bytes]]:
        self.tracker.peer_identities()
        return self._peer_identities

    def peer_identity_key(self) -> Optional[str]:
        self.tracker.peer_identity_key()
        return self._peer_identity_key

    def auth_context(self) -> Mapping[str, Iterable[bytes]]:
        self.tracker.auth_context()
        return self._auth_context

    def time_remaining(self) -> float:
        self.tracker.time_remaining()
        return max(0.0, self._deadline - (time.monotonic() - self._start_time))

    def trailing_metadata(self) -> Sequence[Tuple[str, str]]:
        return self._trailing_metadata

    def code(self) -> str:
        return self._code

    def details(self) -> str:
        return self._details

    def add_done_callback(self, callback: Callable[..., None]) -> None:
        self.tracker.add_done_callback(callback)
        self._callbacks.append(callback)

    def cancelled(self) -> bool:
        self.tracker.cancelled()
        return self._cancelled

    def done(self) -> bool:
        self.tracker.done()
        return self._done
