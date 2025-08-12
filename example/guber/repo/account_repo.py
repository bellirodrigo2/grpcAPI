from datetime import datetime
from typing import Annotated, List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from build.lib.grpcAPI.data_types import ProtoString
from example.guber.db import get_db
from example.guber.lib.account.account_proto_pb2 import AccountInfo, Account
from example.guber.repo.orm.account import Account
from grpcAPI.data_types import Depends

async def get_by_id(id:Annotated[str, ProtoString()],db: Annotated[AsyncSession, Depends(get_db)],) -> Optional[Account]:
    
    async def _get_by_id(id: str, db: AsyncSession) -> Optional[Account]:
        result = await db.execute(
        select(Account).where(Account.account_id == id)
        )
        return result.scalar_one_or_none()

    account = await _get_by_id(id, db)
    if account is None:
        return account
    return Account(
        account_id=account.account_id,
        info=AccountInfo(
            name=account.name,
            email=account.email,
            cpf=account.cpf,
            car_plate=account.car_plate,
            is_driver=account.is_driver
        )
    )

async def create_account(
    account_info: AccountInfo,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> str:
    if account_info.is_driver and not account_info.car_plate:
        raise ValueError("Car plate is required for drivers")
    id = str(uuid4())
    account = Account(
        account_id=id,
        name=account_info.name,
        email=account_info.email,
        cpf=account_info.cpf,
        car_plate=account_info.car_plate,
        is_driver=account_info.is_driver,
        created_at=datetime.now(),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return id

async def list_accounts(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[Account]:
    result = await db.execute(select(Account))
    return result.scalars().all()

async def update_account_field(
    id: str,
    field: str,
    value: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> bool:
    keys = {"name", "email", "cpf"}
    if field not in keys:
        raise ValueError(f"Invalid field. Use {keys}.")

    result = await db.execute(
        select(Account).where(Account.account_id == id)
    )
    account = result.scalar_one_or_none()

    if not account:
        return False

    setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return True
