import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from typing_extensions import Annotated, Any, AsyncIterator, Dict, Generator, List

from grpcAPI.app import APIService, App
from grpcAPI.context import AsyncContext
from grpcAPI.grpcapi import GrpcAPI
from grpcAPI.settings.utils import combine_settings
from grpcAPI.testclient.testclient import TestClient
from grpcAPI.types import Depends, FromContext, FromRequest

# Add 'tests/lib' to sys.path for import resolution
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path.resolve()))
from google.protobuf.descriptor_pb2 import DescriptorProto
from google.protobuf.struct_pb2 import ListValue, Struct
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.wrappers_pb2 import StringValue

from tests.lib.account_pb2 import Account, AccountCreated, AccountInput
from tests.lib.inner.inner_pb2 import InnerMessage
from tests.lib.other_pb2 import Other
from tests.lib.user_pb2 import User, UserCode

root = Path("./tests/proto")


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


def assert_content(protofile_str: str, content: List[str]) -> None:
    for line in content:
        assert line in protofile_str


@pytest.fixture
def serviceapi() -> APIService:
    return APIService(name="service1")


@pytest.fixture
def basic_proto(serviceapi: APIService) -> APIService:

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
def complex_proto(basic_proto: APIService) -> List[APIService]:

    serviceapi2 = APIService(name="service2")

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


@pytest.fixture(scope="session")
def functional_service() -> APIService:
    serviceapi = APIService(
        module="account_service",
        name="functional",
        comments="This is a functional example of a service implementation",
        title="Functional Service",
        description="Service with function implementation",
        tags=["account", "test"],
    )

    @serviceapi(
        title="Create Account",
        description="Create an account by giving a name, email, payload and itens",
        comment="Return the new account id and creation timestamp",
        tags=["account", "creator", "test"],
    )
    async def create_account(
        name: Annotated[str, FromRequest(AccountInput)],
        email: str = FromRequest(AccountInput),
        payload: Dict[str, Any] = FromRequest(AccountInput),
        itens: List[Any] = FromRequest(AccountInput),
    ) -> AccountCreated:

        created_at = datetime(2020, 1, 1)
        ts = Timestamp()
        ts.FromDatetime(created_at)
        country = payload["country"]
        return AccountCreated(
            id=f"id:{name}-{email}-{country}-{itens[0]}", created_at=ts
        )

    @serviceapi
    async def get_accounts(
        values: ListValue, context: AsyncContext
    ) -> AsyncIterator[Account]:

        for v in values:
            if v == "foo":
                context.peer()
            if v == "bar":
                context.set_code("bar")
            if v == "abort":
                await context.abort(35, "abort")
            yield Account(name=v, email=f"{v}@email.com")

    @serviceapi
    async def get_by_ids(ids: AsyncIterator[StringValue]) -> AsyncIterator[Account]:

        async for id in ids:
            yield Account(
                id=id.value, name=f"account{id.value}", email=f"{id.value}@email.com"
            )

    @serviceapi
    async def get_emails(ids: AsyncIterator[StringValue]) -> ListValue:

        emails = ListValue()
        async for id in ids:
            emails.extend([id])
        return emails

    return serviceapi


@pytest.fixture(scope="session")
def app_fixture(functional_service: APIService) -> App:

    app = GrpcAPI()
    app.add_service(functional_service)
    return app


@pytest.fixture(scope="session")
def testclient_fixture(app_fixture: App) -> TestClient:
    settings = combine_settings(
        {
            "path": {
                "proto_path": "tests/proto",
                "lib_path": "tests/lib",
            },
            "compile_proto": {"clean_services": True},
        }
    )
    return TestClient(app_fixture, settings)


class AsyncIt:
    def __init__(self, data: List[Any]) -> None:
        self._data = data
        self._index = 0

    def __aiter__(self) -> "AsyncIt":
        return self

    async def __anext__(self) -> Any:
        if self._index >= len(self._data):
            raise StopAsyncIteration
        value = self._data[self._index]
        self._index += 1
        return value
