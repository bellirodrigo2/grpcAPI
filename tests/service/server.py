# server.py
import asyncio
import sys
from pathlib import Path
from typing import Annotated, List

import grpc

from grpcAPI.ctxinject.inject import get_mapped_ctx, inject_args, resolve_mapped_ctx
from grpcAPI.proto_inject import FromContext, FromRequest
from grpcAPI.proto_proxy import (
    ProtoProxy,
    bind_proto_proxy,
    import_py_files_from_folder,
)
from grpcAPI.proxy import IteratorProxy
from grpcAPI.types import BaseEnum, Context, Int32, OneOf, Stream


class user_code(BaseEnum):
    EMPLOYEE = 0
    SCHOOL = -247
    INACTIVE = 1


class baseproto(ProtoProxy):

    @classmethod
    def protofile(cls) -> str:
        return "service"


class user_input(baseproto):
    code: user_code
    age: int
    name: str
    affilliation: str


class user(baseproto):
    age: int
    id: int
    name: str
    employee: Annotated[str, OneOf("occupation")]
    school: Annotated[str, OneOf("occupation")]
    inactive: Annotated[bool, OneOf("occupation")]


class user_list(baseproto):
    users: List[user]
    index: Int32


class names_id(baseproto):
    ids: List[int]


source_folder = Path(__file__).parent.parent
p = source_folder / "proto2" / "compiled"
sys.path.append(str(p))

modules = import_py_files_from_folder(p, f"{source_folder.name}.proto2.compiled")
bind_proto_proxy(user_input, modules)
bind_proto_proxy(user, modules)
bind_proto_proxy(user_list, modules)
bind_proto_proxy(names_id, modules)

service_grpc = modules["service_grpc"]


async def newuser(
    request: user_input,
    userage: str = FromRequest(model=user_input, field="age"),
    peer: str = FromContext(),
) -> user:
    userproxy = user(age=userage, id=0, name=request.name)

    key = request.code.name.lower()
    if key not in ("employee", "school", "inactive"):
        raise ValueError(f"Occupation = {key}")
    affiliation = (
        request.affilliation if key != "inactive" else bool(request.affilliation)
    )
    setattr(userproxy, key, affiliation)
    print(f"Received newuser: '{userproxy}' from: '{peer}'")

    return userproxy


async def manynewuser(request: Stream[user_input], ctx: Context) -> user_list:

    users = []
    try:
        async for req in request:
            user_obj = await newuser(req, req.age, ctx.peer())
            users.append(user_obj)
    except Exception as e:
        print(f"[Server] Error in manynewuser: {e}")
        raise

    return user_list(users=users, index=0)


async def getusers(request: names_id) -> Stream[user]:
    print(f"getusers called with ids: {request.ids}")
    for i in request.ids:
        yield user(age=30 + i, id=i, name=f"User {i}", inactive=True)


async def bilateralnewuser(request: Stream[user_input], ctx: Context) -> Stream[user]:
    async for req in request:
        print(f"Bilateral stream received: {req}")
        yield user(age=req.age, id=req.code, name=req.name, employee="StreamInc")


class UserService(service_grpc.user_serviceServicer):

    def __init__(self, newuser_mapped) -> None:
        self.newuser_mapped = newuser_mapped

    async def newuser(self, request, context):

        proxyreq = user_input(request)
        ctx = {user_input: proxyreq, Context: context}
        kwargs = await resolve_mapped_ctx(ctx, self.newuser_mapped)
        proxy_response = await newuser(**kwargs)
        return proxy_response.unwrap

    async def manynewuser(self, request_iterator, context):
        req_iter = IteratorProxy(request_iterator, user_input)
        ctx = {Stream[user_input]: req_iter, Context: context}

        func = await inject_args(manynewuser, ctx)

        proxy_response = await func()
        return proxy_response.unwrap

    async def getusers(self, request, context):
        proxyreq = names_id(request)
        ctx = {names_id: proxyreq, Context: context}
        func = await inject_args(getusers, ctx)

        async for resp in func():
            yield resp.unwrap

    async def bilateralnewuser(self, request_iterator, context):
        req_iter = IteratorProxy(request_iterator, user_input)
        ctx = {Stream[user_input]: req_iter, Context: context}

        func = await inject_args(bilateralnewuser, ctx)

        async for resp in func():
            yield resp.unwrap


async def serve():
    server = grpc.aio.server()

    mapped = await get_mapped_ctx(newuser, {user_input: None, Context: None})
    service = UserService(mapped)
    service_grpc.add_user_serviceServicer_to_server(service, server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("Server started on :50051")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
