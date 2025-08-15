from typing import Any, Callable, Optional


from grpcAPI.app import APIPackage
from grpcAPI.data_types import FromRequest

from example.guber.server.application.repo import AccountRepo, get_account_repo
from example.guber.server.domain import Account, AccountInfo


account_package = APIPackage("account")


class FromAccountInfo(FromRequest):
    def __init__(self, field: Optional[str] = None, validator: Callable[..., Any] | None = None, **meta: Any):
        super().__init__(AccountInfo, field, validator, **meta)

__all__ = [
    "account_package",
    "AccountRepo",
    "get_account_repo",
    "Account",
    "AccountInfo",
    "FromAccountInfo",
]
