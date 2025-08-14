from typing_extensions import Any, Iterable, Optional, Protocol

from example.guber.packages.account import Account
from example.guber.domain.models import CPF, CarPlate, EmailStr


class AccountRepo(Protocol):

    async def get_by_id(self, id: str) -> Optional[Account]: ...

    async def exist_email(self, email: EmailStr) -> bool: ...

    async def exist_cpf(self, cpf: CPF) -> bool: ...

    async def create_account(
        self, name: str, email: EmailStr, cpf: CPF, car_plate: CarPlate, is_driver: bool
    ) -> str: ...

    async def list_accounts(self, ids: Iterable[str]) -> Iterable[Account]: ...

    async def update_account_field(self, id: str, field: str, value: str) -> bool: ...


async def get_account_repo(**kwargs: Any) -> AccountRepo:  # type: ignore
    pass
