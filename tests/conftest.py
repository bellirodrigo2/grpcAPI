import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator, Generator, List

import pytest
from typing_extensions import Annotated

from grpcAPI.app import BaseService
from grpcAPI.extract_types import extract_request_response_type
from grpcAPI.types.injects import Depends, FromContext, FromRequest
from tests.lib.inner.inner_pb2 import InnerMessage

# Add 'tests/lib' to sys.path for import resolution
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path.resolve()))
from google.protobuf.descriptor_pb2 import DescriptorProto
from google.protobuf.timestamp_pb2 import Timestamp

from tests.lib.other_pb2 import Other
from tests.lib.user_pb2 import User, UserCode

root = Path("./tests/proto")


def assert_content(protofile_str: str, content: List[str]) -> None:
    for line in content:
        assert line in protofile_str


@pytest.fixture
def serviceapi() -> BaseService:
    return BaseService(name="service1", extract_metatypes=extract_request_response_type)


@pytest.fixture
def basic_proto(serviceapi: BaseService) -> BaseService:

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

    return serviceapi


@pytest.fixture
def complex_proto(basic_proto: BaseService) -> List[BaseService]:

    serviceapi2 = BaseService(
        name="service2", extract_metatypes=extract_request_response_type
    )

    @serviceapi2
    async def unary(req: User) -> DescriptorProto:
        pass

    @serviceapi2
    async def clientstream(req: AsyncIterator[DescriptorProto]) -> Other:
        pass

    @serviceapi2
    async def serverstream(req: Other) -> AsyncIterator[Timestamp]:
        yield User()

    @serviceapi2
    async def bilateral(req: AsyncIterator[Timestamp]) -> AsyncIterator[User]:
        yield User()

    serviceapi3 = BaseService(
        name="service3",
        package="pack3",
        module="mod3",
        extract_metatypes=extract_request_response_type,
    )

    @serviceapi3
    async def unary(req: User) -> DescriptorProto:
        pass

    @serviceapi3
    async def clientstream(req: AsyncIterator[DescriptorProto]) -> Other:
        pass

    return [basic_proto, serviceapi2, serviceapi3]


@pytest.fixture
def inject_proto() -> BaseService:

    serviceapi = BaseService(
        name="injected", extract_metatypes=extract_request_response_type
    )

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


@pytest.fixture
def temp_dir() -> Generator[Path, Any, None]:
    source_dir = Path("tests/proto")

    temp_dir = Path(tempfile.mkdtemp())
    # print(f"[SETUP] Move files from '{source_dir}' to '{temp_dir}'")

    temp_proto = temp_dir / "proto"
    temp_proto.mkdir(parents=True, exist_ok=True)

    if source_dir.exists():
        shutil.copytree(source_dir, temp_proto, dirs_exist_ok=True)
    else:
        raise FileNotFoundError(f"Source folder not found: {source_dir}")

    yield temp_dir

    # print(f"[TEARDOWN] Cleaning temporary folder {temp_dir}")
    shutil.rmtree(temp_dir)
