# context_mock.py
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from grpcAPI.exceptionhandler import ErrorCode
from grpcAPI.types import Context

std_auth_context = {
    "x509_common_name": [b"default-client"],
    "transport_security_type": [b"ssl"],
}


class ContextMock(Context):
    def __init__(
        self,
        peer: str = "127.0.0.1:12345",
        invocation_metadata: Optional[Sequence[Any]] = None,
        peer_identities: Optional[Sequence[Any]] = None,
        peer_identity_key: Optional[str] = None,
        trailing_metadata: Optional[Sequence[Any]] = None,
        code: Optional[Any] = None,
        details: Optional[str] = None,
        deadline: Optional[float] = 60.0,
        auth_context: Optional[Dict[str, Any]] = None,
    ):
        self._peer = peer
        self._invocation_metadata = invocation_metadata or []
        self._peer_identities = peer_identities
        self._peer_identity_key = peer_identity_key

        self._trailing_metadata = trailing_metadata or []
        self._code = code
        self._details = details
        self._aborted = False
        self._cancelled = False
        self._abort_code: Optional[ErrorCode] = None
        self._abort_details: Optional[str] = None

        self._start_time = time.monotonic()
        self._deadline = deadline

        self._callbacks: List[Callable[[], None]] = []

        self._auth_context = auth_context or std_auth_context

    def peer(self) -> str:
        return self._peer

    def peer_identities(self) -> Optional[Sequence[Any]]:
        return self._peer_identities

    def peer_identity_key(self) -> Optional[str]:
        return self._peer_identity_key

    def invocation_metadata(self) -> Sequence[Any]:
        return self._invocation_metadata

    def set_trailing_metadata(self, metadata: Sequence[Any]) -> None:
        self._trailing_metadata = metadata

    def trailing_metadata(self) -> Sequence[Any]:
        return self._trailing_metadata

    def abort(self, code: Any, details: str) -> None:
        self._aborted = True
        self._abort_code = code
        self._abort_details = details
        raise RuntimeError(f"gRPC aborted with code={code}, details={details}")

    def abort_with_status(self, status: ErrorCode) -> None:
        self._aborted = True
        self._abort_code = getattr(status, "code", None)
        self._abort_details = getattr(status, "details", str(status))
        raise RuntimeError(f"Aborted with status: {status}")

    def was_aborted(self) -> bool:
        return self._aborted

    def abort_info(self) -> Tuple[Optional[ErrorCode], Optional[str]]:
        return self._abort_code, self._abort_details

    def set_code(self, code: Any) -> None:
        self._code = code

    def set_details(self, details: str) -> None:
        self._details = details

    def code(self) -> Optional[ErrorCode]:
        return self._code

    def details(self) -> Optional[str]:
        return self._details

    def cancel(self) -> None:
        self._cancelled = True
        for cb in self._callbacks:
            cb()

    def is_active(self) -> bool:
        return not self._cancelled and not self._aborted

    def time_remaining(self) -> float:
        if self._deadline is None:
            return float("inf")
        elapsed = time.monotonic() - self._start_time
        return max(0.0, self._deadline - elapsed)

    def add_callback(self, callback: Callable[[], None]) -> bool:
        self._callbacks.append(callback)
        return True

    def set_compression(self, compression: int) -> None:
        raise NotImplementedError

    def disable_next_message_compression(self) -> None:
        raise NotImplementedError

    def send_initial_metadata(
        self, initial_metadata: Sequence[Tuple[str, str]]
    ) -> None:
        raise NotImplementedError

    def auth_context(self) -> Dict[str, Any]:
        raise NotImplementedError
