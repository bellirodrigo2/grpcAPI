from example.guber.repo.account_repo import AccountRepo, get_account_repo
from example.guber.domain import Account, AccountInfo
from grpcAPI.app import APIPackage

account_package = APIPackage("account")

__all__ = [
    "account_package",
    "AccountRepo",
    "get_account_repo",
    "Account",
    "AccountInfo",
]
