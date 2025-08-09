from typing import AsyncIterator, List, Set

import pytest
from typing_extensions import Annotated

from grpcAPI.app import APIService
from grpcAPI.data_types import Depends, FromContext, FromRequest
from grpcAPI.makeproto.write_proto import write_protos
from grpcAPI.process_service.inject_typing import InjectProtoTyping
from grpcAPI.proto_build import make_protos
from tests.conftest import (
    DescriptorProto,
    InnerMessage,
    Other,
    Timestamp,
    User,
    UserCode,
    root,
)


def assert_content(protofile_str: str, content: List[str]) -> None:
    for line in content:
        assert line in protofile_str


@pytest.fixture
def basic_proto() -> APIService:

    serviceapi = APIService(name="service1")

    @serviceapi
    async def unary(req: User) -> User:
        pass

    @serviceapi
    async def clientstream(req: AsyncIterator[User]) -> Other:
        pass

    @serviceapi
    async def serverstream(req: Other) -> AsyncIterator[User]:
        yield User()

    @serviceapi
    async def bilateral(req: AsyncIterator[Other]) -> AsyncIterator[User]:
        yield User()

    inject_proto_processing = InjectProtoTyping()
    inject_proto_processing.process(serviceapi)
    return serviceapi


@pytest.fixture
def complex_proto(basic_proto: APIService) -> List[APIService]:

    serviceapi2 = APIService(name="service2")

    @serviceapi2
    async def unary2(req: User) -> DescriptorProto:
        pass

    @serviceapi2
    async def clientstream2(req: AsyncIterator[DescriptorProto]) -> Other:
        pass

    @serviceapi2
    async def serverstream2(req: Other) -> AsyncIterator[Timestamp]:
        yield User()

    @serviceapi2
    async def bilateral2(req: AsyncIterator[Timestamp]) -> AsyncIterator[User]:
        yield User()

    serviceapi3 = APIService(
        name="service3",
        package="pack3",
        module="mod3",
    )

    @serviceapi3
    async def unary(req: User) -> DescriptorProto:
        pass

    @serviceapi3
    async def clientstream(req: AsyncIterator[DescriptorProto]) -> Other:
        pass

    return [basic_proto, serviceapi2, serviceapi3]


@pytest.fixture
def inject_proto() -> APIService:

    serviceapi = APIService(name="injected")

    async def get_db() -> str:
        return "sqlite"

    @serviceapi
    async def unary(
        code: Annotated[UserCode, FromRequest(User)],
        age: InnerMessage = FromRequest(User),
        db: str = Depends(get_db),
    ) -> User:
        pass

    @serviceapi
    async def clientstream(req: AsyncIterator[User]) -> Other:
        pass

    @serviceapi
    async def serverstream(
        name: Annotated[str, FromRequest(Other, "name")], peer: str = FromContext()
    ) -> AsyncIterator[User]:
        yield User()

    @serviceapi
    async def bilateral(
        req: AsyncIterator[Other], fromctx: str = FromContext(field="peer")
    ) -> AsyncIterator[User]:
        yield User()

    return serviceapi


def test_basic_content(basic_proto: APIService) -> None:

    contents = [
        'syntax = "proto3";',
        'import "user.proto";',
        'import "other.proto";',
        "service service1 {",
        "rpc unary(userpack.User) returns (userpack.User);",
        "rpc clientstream(stream userpack.User) returns (Other);",
        "rpc serverstream(Other) returns (stream userpack.User);",
        "rpc bilateral(stream Other) returns (stream userpack.User);",
    ]
    proto_stream = make_protos(
        {"pack1": [basic_proto]},
    )
    proto_list = list(proto_stream)
    for proto in proto_list:
        assert_content(proto.content, contents)

    def run_write_protos() -> Set[str]:
        return write_protos(
            proto_stream=proto_list,
            out_dir=root,
            overwrite=False,
            clean_services=True,
        )

    pack = run_write_protos()

    assert pack == {"service.proto"}
    all_items_recursive = [
        str(f.relative_to(root).as_posix())
        for f in list(root.rglob("*"))
        if f.is_file()
    ]
    assert "other.proto" in all_items_recursive
    assert "user.proto" in all_items_recursive
    assert "service.proto" in all_items_recursive
    assert "inner/inner.proto" in all_items_recursive

    with pytest.raises(FileExistsError):
        run_write_protos()


def test_complex(complex_proto: List[APIService]) -> None:

    service1, service2, service3 = complex_proto

    services = {"": [service1, service2], "pack3": [service3]}

    proto_stream = make_protos(
        services,
    )

    pack = write_protos(
        proto_stream=proto_stream,
        out_dir=root,
        overwrite=True,
        clean_services=True,
    )

    assert pack == {"pack3/mod3.proto", "service.proto"}
    all_items_recursive = [
        str(f.relative_to(root).as_posix())
        for f in list(root.rglob("*"))
        if f.is_file()
    ]
    assert "other.proto" in all_items_recursive
    assert "user.proto" in all_items_recursive
    assert "service.proto" in all_items_recursive
    assert "inner/inner.proto" in all_items_recursive
    assert "pack3/mod3.proto" in all_items_recursive


def test_inject(inject_proto: APIService) -> None:

    services = {"": [inject_proto]}
    proto_stream = make_protos(
        services,
    )
    pack = write_protos(
        proto_stream=proto_stream,
        out_dir=root,
        overwrite=True,
        clean_services=True,
    )
    assert pack == {"service.proto"}
    all_items_recursive = [
        str(f.relative_to(root).as_posix())
        for f in list(root.rglob("*"))
        if f.is_file()
    ]
    assert "other.proto" in all_items_recursive
    assert "user.proto" in all_items_recursive
    assert "service.proto" in all_items_recursive
    assert "inner/inner.proto" in all_items_recursive
