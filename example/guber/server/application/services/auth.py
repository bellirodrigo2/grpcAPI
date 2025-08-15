from typing_extensions import Annotated,Any

from grpcAPI.data_types import Depends


async def async_authentication(**kwargs: Any) -> None:
    pass

Authenticate = Annotated[None, Depends(async_authentication, order=0)]