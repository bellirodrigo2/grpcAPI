from typing_extensions import Any, Iterable, Optional, Protocol

from example.guber.application.usecase.account import Account,AccountInfo


class AccountRepo(Protocol):

    async def get_by_id(self, id: str) -> Optional[Account]: ...

    async def exist_email(self, email: str) -> bool: ...

    async def exist_cpf(self, cpf: str) -> bool: ...

    async def create_account(self,account_info:AccountInfo) -> str: ...

    async def list_accounts(self, ids: Iterable[str]) -> Iterable[Account]: ...

    async def update_account_field(self, id: str, field: str, value: str) -> bool: ...


async def get_account_repo(**kwargs: Any) -> AccountRepo:  # type: ignore
    pass
