# server.py
import asyncio
from pathlib import Path
from typing import Annotated

import grpc

import tests.proto2.compiled.service_pb2 as pb2
import tests.proto2.compiled.service_pb2_grpc as pb2_grpc
from grpcAPI.ctxinject.inject import inject_args
from grpcAPI.proto_inject import FromContext, FromRequest
from grpcAPI.proto_proxy import (
    ProtoProxy,
    bind_proto_proxy,
    import_py_files_from_folder,
)
from grpcAPI.types import BaseEnum, Context
from grpcAPI.types.base import OneOf


class user_code(BaseEnum):
    EMPLOYEE = 0
    STUDENT = -247
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


source_folder = Path(__file__).parent.parent
p = source_folder / "proto2" / "compiled"

modules = import_py_files_from_folder(p, f"{source_folder.name}.proto2.compiled")
bind_proto_proxy(user_input, modules)
bind_proto_proxy(user, modules)


async def newuser(
    request: user_input,
    userage: str = FromRequest(model=user_input, field="age"),
    peer: str = FromContext(),
) -> user:
    userproxy = user(age=userage, id=0, name=request.name)

    key = request.code.name.lower()
    if key not in ("employee", "student", "inactive"):
        raise ValueError(f"Occupation = {key}")

    setattr(userproxy, key, request.affilliation)
    print(f"Received newuser: '{userproxy}' from: '{peer}'")

    return userproxy


class UserService(pb2_grpc.user_serviceServicer):

    async def newuser(self, request, context):

        proxyreq = user_input(request)
        ctx = {user_input: proxyreq, Context: context}
        func = await inject_args(newuser, ctx)

        proxy_response = await func()
        return proxy_response.unwrap

    async def manynewuser(self, request_iterator, context):
        users = []
        async for req in request_iterator:
            print(f"Received manynewuser item: {req}")
            u = pb2.user(
                age=req.age, id=len(users) + 1, name=req.name, school="School X"
            )
            users.append(u)
        return pb2.user_list(users=users, index=42)

    async def getusers(self, request, context):
        print(f"getusers called with ids: {request.ids}")
        for i in request.ids:
            yield pb2.user(age=30 + i, id=i, name=f"User {i}", inactive=True)

    async def bilateralnewuser(self, request_iterator, context):
        async for req in request_iterator:
            print(f"Bilateral stream received: {req}")
            yield pb2.user(
                age=req.age, id=req.code, name=req.name, employer="StreamInc"
            )


async def serve():
    server = grpc.aio.server()
    pb2_grpc.add_user_serviceServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("Server started on :50051")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
