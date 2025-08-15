from collections.abc import Iterable
from datetime import datetime
from typing import Any as Any, AsyncGenerator,  Optional

from sqlalchemy import select

from example.guber.server.domain import AccountInfo, Account
from example.guber.server.application.repo.account_repo import AccountRepo
from example.guber.server.adapters.repo.sqlalchemy import get_db,AccountDB, SqlAlchemyDB


class SqlAlchemyAccountRepo(AccountRepo, SqlAlchemyDB):
    
    async def get_by_id(self, id: str) -> Optional[Account]:
        result = await self.db.execute(select(AccountDB).where(AccountDB.account_id == id))
        account= result.scalar_one_or_none()
        if account is None:
            return account
        return orm_to_proto_account(account)


    async def exist_email(self, email: str) -> bool:
        result = await self.db.execute(select(AccountDB).where(AccountDB.email == email))
        return result.scalar_one_or_none() is not None

    async def exist_cpf(self, cpf: str) -> bool:
        result = await self.db.execute(select(AccountDB).where(AccountDB.cpf == cpf))
        return result.scalar_one_or_none() is not None

    async def create_account(self, id:str, account_info:AccountInfo) -> str:
        account = proto_to_orm_account(account_info)
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return id


    async def list_accounts(self, ids: Iterable[str]) -> Iterable[Account]:
        result = await self.db.execute(select(AccountDB))
        accounts = result.scalars().all()
        return [orm_to_proto_account(account) for account in accounts]

    async def update_account_field(self, id: str, field: str, value: str) -> bool:
        keys = {"name", "email", "cpf"}
        if field not in keys:
            raise ValueError(f"Invalid field. Use {keys}.")

        result = await self.db.execute(select(AccountDB).where(AccountDB.account_id == id))
        account = result.scalar_one_or_none()

        if not account:
            raise ValueError(f"Account with id '{id}' not found")

        setattr(account, field, value)
        await self.db.commit()
        await self.db.refresh(account)
        return True


async def get_account_sqlalchemy_repo()->AsyncGenerator[SqlAlchemyAccountRepo, None]:
    async with get_db() as db:
        yield SqlAlchemyAccountRepo(db)


def proto_to_orm_account(account: AccountInfo) -> AccountDB:
    return AccountDB(
        account_id=str(uuid4()),
        name=account.name,
        email=account.email,
        cpf=account.cpf,
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
            cpf=account.cpf,
            car_plate=account.car_plate,
            is_driver=account.is_driver,
        ),
    )