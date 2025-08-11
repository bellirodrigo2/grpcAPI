from typing import Any, Optional
from typing_extensions import Annotated
from example.guber.account import account_package
from example.guber.account.repo import  create_account
from example.guber.lib.account.account_proto_pb2 import AccountInfo
from example.guber.models.vos import  CPF, CarPlate, EmailStr
from grpcAPI.data_types import Depends, FromRequest
from google.protobuf.wrappers_pb2 import StringValue

user_module = account_package.make_module("user")

class FromAccountInfo(FromRequest):
    def __init__(self, field: Optional[str] = None, **meta: Any):
        super().__init__(model=AccountInfo, field=field, **meta)

# signup user
signup_service = user_module.make_service("signup")

@signup_service
async def signup_user(
    email:Annotated[EmailStr,FromAccountInfo(field="email")], 
    cpf:Annotated[CPF,FromAccountInfo('cpf')], 
    car_plate:Annotated[CarPlate,FromAccountInfo('carPlate')],
    user_id: Annotated[str, Depends(create_account)],
    )->StringValue:
    
	return StringValue(value=str(user_id))


# signin user

# update user

# delete user
