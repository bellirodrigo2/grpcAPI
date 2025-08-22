from typing import Awaitable, Callable

from example.guber.server.application.repo import AccountRepository


async def is_passenger(account_repo: AccountRepository) -> Callable[[str], Awaitable[bool]]:
    async def _is_passenger(id: str) -> bool:
        account = await account_repo.get_by_id(id)
        return account is not None and not account.info.is_driver

    return _is_passenger
