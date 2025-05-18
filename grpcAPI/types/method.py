from typing import AsyncGenerator, TypeVar

T = TypeVar("T")

Stream = AsyncGenerator[T, None]

# async def unary_call(request: UserRequest) -> UserResponse:
#     pass
# async def client_stream(stream: Stream[FileChunk]) -> UploadSummary:
#     pass
# async def serverStream(request: ItemQuery) -> Stream[ItemResponse]:
#     pass
# async def bi_direct_stream(stream: Stream[FileChunk]) -> Stream[UploadSummary]:
#     pass
