from typing import Any, Optional

from example.guber.db import get_db
from example.guber.models import CPF, CarPlate, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from google.protobuf.wrappers_pb2 import StringValue
from typing_extensions import Annotated

from example.guber.account import account_package
from example.guber.repo.account_repo import create_account, get_by_id, update_account_field
from example.guber.lib.account.account_proto_pb2 import Account, AccountInfo
from grpcAPI.data_types import AsyncContext, Depends, FromRequest
from grpcAPI.prototypes.lib.prototypes_pb2 import KeyValueStr

user_module = account_package.make_module("user")


class FromAccountInfo(FromRequest):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=AccountInfo, field=field, **meta)


# signup user
account_services = user_module.make_service("account_services")

async def auth_plchdr(ctx:AsyncContext)->bool:
    # Placeholder for authentication logic
    return True

@account_services
async def signup_user(
    cpf: Annotated[CPF, FromAccountInfo()],
    email: Annotated[EmailStr, FromAccountInfo()],
    car_plate: Annotated[CarPlate, FromAccountInfo()],
    user_id: Annotated[str, Depends(create_account)],
    auth:Annotated[bool, Depends(auth_plchdr)]
) -> StringValue:
    #cpf, email and car_plate are here for validation, and to define the input protobuf class
    return StringValue(value=str(user_id))


@account_services(request_type_input=StringValue)
async def get_account(account: Annotated[Optional[Account], Depends(get_by_id)],) -> Account:
    if account is None:
        raise ValueError("Account not found")
    return account
    
class FromKeyValue(FromRequest):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=KeyValueStr, field=field, **meta)

@account_services
async def update_car_plate(id:Annotated[str, FromKeyValue('key')],car_plate:Annotated[CarPlate,FromKeyValue('value')],db: Annotated[AsyncSession, Depends(get_db)],) -> None:
    updated = await update_account_field(id, "car_plate", str(car_plate), db)   
    if not updated:
        raise ValueError(f"Account with id {id} not found or car plate not updated")
