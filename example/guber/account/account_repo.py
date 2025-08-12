from datetime import datetime
from typing import Annotated, List, Optional
from uuid import uuid4

from pydantic import EmailStr
from sqlalchemy.orm import Session

from example.guber.account.user import FromAccountInfo
from example.guber.db import get_db
from example.guber.lib.account.account_proto_pb2 import AccountInfo
from example.guber.models.account import Account
from example.guber.models.vos import CPF, CarPlate
from grpcAPI.data_types import Depends


async def get_by_id(id: str, db: Session) -> Optional[Account]:
    return db.query(Account).filter(Account.account_id == id).first()


async def get_by_email(email: EmailStr, db: Session) -> Optional[Account]:
    return db.query(Account).filter(Account.email == email).first()


async def account_exist(
    email: Annotated[EmailStr, FromAccountInfo()],
    db: Annotated[Session, Depends(get_db)],
) -> Optional[Session]:
    if await get_by_email(email=email, db=db):
        return db
    return None


async def create_account(
    account_info: AccountInfo,
    cpf: Annotated[CPF, FromAccountInfo("cpf")],
    car_plate: Annotated[CarPlate, FromAccountInfo("carPlate")],
    db: Annotated[Optional[Session], Depends(account_exist)],
) -> str:
    if db is None:
        raise ValueError("Account with this email already exists")
    id = str(uuid4())
    account = Account(
        account_id=id,
        name=account_info.name,
        email=account_info.email,
        cpf=cpf,
        car_plate=car_plate,
        is_driver=account_info.is_driver,
        created_at=datetime.now(),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return id


async def list_accounts(db: Annotated[Session, Depends(get_db)]) -> List[Account]:
    return db.query(Account).all()
