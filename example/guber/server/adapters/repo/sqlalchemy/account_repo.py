from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy import select
from typing_extensions import Iterable, Optional

from example.guber.server.adapters.repo.sqlalchemy.db import (
    AsyncSessionLocal,
    SqlAlchemyDB,
)
from example.guber.server.adapters.repo.sqlalchemy.orm.account import AccountDB
from example.guber.server.application.repo.account_repo import AccountRepo
from example.guber.server.domain import Account, AccountInfo


class SqlAlchemyAccountRepo(SqlAlchemyDB, AccountRepo):

    async def get_by_id(self, id: str) -> Optional[Account]:
        result = await self.db.execute(
            select(AccountDB).where(AccountDB.account_id == id)
        )
        account = result.scalar_one_or_none()
        if account is None:
            return account
        return orm_to_proto_account(account)

    async def exist_email(self, email: str) -> bool:
        result = await self.db.execute(
            select(AccountDB).where(AccountDB.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def exist_sin(self, sin: str) -> bool:
        result = await self.db.execute(select(AccountDB).where(AccountDB.sin == sin))
        return result.scalar_one_or_none() is not None

    async def create_account(self, id: str, account_info: AccountInfo) -> str:
        account = proto_to_orm_account(id, account_info)
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return id

    async def list_accounts(self, ids: Iterable[str]) -> Iterable[Account]:
        result = await self.db.execute(select(AccountDB))
        accounts = result.scalars().all()
        return [orm_to_proto_account(account) for account in accounts]

    async def update_account_field(self, id: str, field: str, value: str) -> bool:
        keys = {"name", "email", "car_plate"}
        if field not in keys:
            raise ValueError(f"Invalid field. Use {keys}.")

        result = await self.db.execute(
            select(AccountDB).where(AccountDB.account_id == id)
        )
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"Account with id '{id}' not found")

        setattr(account, field, value)
        await self.db.commit()
        await self.db.refresh(account)
        return True


def proto_to_orm_account(id: str, account: AccountInfo) -> AccountDB:
    return AccountDB(
        account_id=id,
        name=account.name,
        email=account.email,
        sin=account.sin,
        car_plate=account.car_plate,
        is_driver=account.is_driver,
        created_at=datetime.now(),
    )


def orm_to_proto_account(account: AccountDB) -> Account:
    return Account(
        account_id=account.account_id,
        info=AccountInfo(
            name=account.name,
            email=account.email,
            sin=account.sin,
            car_plate=account.car_plate,
            is_driver=account.is_driver,
        ),
    )


@asynccontextmanager
async def get_account_sqlalchemy_repo():
    db = AsyncSessionLocal()
    try:
        yield SqlAlchemyAccountRepo(db)
    finally:
        await db.close()
