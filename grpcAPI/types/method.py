from collections.abc import AsyncIterator
from typing import Any, Optional, TypeVar, get_args, get_origin

T = TypeVar("T")

Stream = AsyncIterator[T]


def if_stream_get_type(bt: type[Any]) -> Optional[type[Any]]:
    if get_origin(bt) is AsyncIterator:
        return get_args(bt)[0]
    return None


# async def unary_call(request: UserRequest) -> UserResponse:
#     pass
# async def client_stream(stream: Stream[FileChunk]) -> UploadSummary:
#     pass
# async def serverStream(request: ItemQuery) -> Stream[ItemResponse]:
#     pass
# async def bi_direct_stream(stream: Stream[FileChunk]) -> Stream[UploadSummary]:
#     pass
