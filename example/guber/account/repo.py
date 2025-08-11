


from pydantic import EmailStr
from pytest import Session
from typing_extensions import Annotated

from build.lib.grpcAPI.data_types import Depends
from example.guber.account.user import FromAccountInfo
from example.guber.db import get_db
from example.guber.lib.account.account_proto_pb2 import AccountInfo

async def account_exist(email:Annotated[EmailStr,FromAccountInfo()],db: Annotated[Session, Depends(get_db)])->bool:
    return True
 
async def create_account(account_info: AccountInfo, _: Annotated[bool, Depends(account_exist)])->str:
    return 'id'