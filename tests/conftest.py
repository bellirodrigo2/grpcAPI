# ruff: noqa: E402
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Iterable,
    Optional,
    Sequence,
    Type,
    get_args,
    get_origin,
)

import pytest
from google.protobuf.descriptor_pb2 import DescriptorProto  # noqa: F401
from google.protobuf.empty_pb2 import Empty
from google.protobuf.struct_pb2 import ListValue, Struct
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.wrappers_pb2 import BytesValue, StringValue  # noqa: F401
from typing_extensions import Annotated, Dict, List

from grpcAPI import ErrorCode
from grpcAPI.app import APIService, App
from grpcAPI.grpcapi import GrpcAPI
from grpcAPI.makeproto.interface import ILabeledMethod, IMetaType, IService
from grpcAPI.protoc_compile import compile_protoc
from grpcAPI.settings.utils import combine_settings
from grpcAPI.testclient.testclient import TestClient
from grpcAPI.types import AsyncContext, FromRequest

lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path.resolve()))

from tests.lib.account_pb2 import Account, AccountCreated, AccountInput
from tests.lib.inner.inner_pb2 import InnerMessage  # noqa: F401
from tests.lib.multi.inner.class_pb2 import ClassMsg  # noqa: F401
from tests.lib.other_pb2 import Other  # noqa: F401
from tests.lib.user_pb2 import User, UserCode  # noqa: F401

root = Path("./tests/proto")

logger = logging.getLogger("grpcAPI.server")


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
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."

    @serviceapi(
        title="Create Account",
        description="Create an account by giving a name, email, payload and itens",
        comment=text,
        tags=["account", "creator", "test"],
    )
    async def create_account(
        name: Annotated[str, FromRequest(AccountInput)],
        context: AsyncContext,
        email: str = FromRequest(AccountInput),
        payload: Dict[str, Any] = FromRequest(AccountInput),
        itens: List[Any] = FromRequest(AccountInput),
    ) -> AccountCreated:
        if name == "raise":
            raise NotImplementedError("Not Implemented Test")
        if name == "abort":
            await context.abort(35, "abort")

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
            if v == "raise":
                raise NotImplementedError("Not Implemented Test")
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
def account_input() -> Dict[str, Any]:
    name = "John"
    email = "john@email.com"
    country = "BR"
    struct = Struct()
    struct.update({"country": country, "size": 125})
    itens = ListValue()
    list_ = ["foo"]
    itens.extend(list_)

    request = AccountInput(name=name, email=email, payload=struct, itens=itens)
    return {
        "name": name,
        "email": email,
        "country": country,
        "struct": struct,
        "itens": itens,
        "request": request,
    }


@pytest.fixture(scope="session")
def app_fixture(functional_service: APIService) -> App:

    app = GrpcAPI()
    app.add_service(functional_service)

    @app.exception_handler(NotImplementedError)
    async def handle_not_implemented(
        exc: NotImplementedError, context: AsyncContext
    ) -> None:
        context.set_code(500)
        await context.abort(ErrorCode.ABORTED, str(exc))

    return app


@pytest.fixture(scope="session")
def testclient_fixture(app_fixture: App) -> TestClient:
    settings = combine_settings(
        {
            "proto_path": "tests/proto",
            "lib_path": "tests/lib",
            "compile_proto": {"clean_services": True},
            "format": {"case": "none", "comment_style": "multiline"},
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


# ---------------- MAKE PROTO--------------------


class MetaType:
    def __init__(
        self,
        argtype: Type[Any],
        basetype: Type[Any],
        origin: Optional[Type[Any]],
        package: str,
        proto_path: str,
    ) -> None:
        self.argtype = argtype
        self.basetype = basetype
        self.origin = origin
        self.package = package
        self.proto_path = proto_path


def get_protofile_path(cls: Type[Any]) -> str:
    return cls.DESCRIPTOR.file.name


def get_package(cls: Type[Any]) -> str:
    return cls.DESCRIPTOR.file.package


Empty.package = get_package(Empty)
Empty.proto_path = get_protofile_path(Empty)


def make_metatype_from_type(
    argtype: Type[Any],
) -> IMetaType:
    origin = get_origin(argtype)
    basetype = argtype if origin is None else get_args(argtype)[0]
    package = getattr(basetype, "package", "")
    proto_path = getattr(basetype, "proto_path", "")
    return MetaType(
        argtype=argtype,
        basetype=basetype,
        origin=origin,
        package=package,
        proto_path=proto_path,
    )


empty_instance = make_metatype_from_type(Empty)
empty_iterator = make_metatype_from_type(AsyncIterator[Empty])


async def ping(req: Empty) -> Empty:
    return Empty()


async def ping_client_stream(req: AsyncIterator[Empty]) -> Empty:
    return Empty()


async def ping_server_stream(req: Empty) -> AsyncIterator[Empty]:
    yield Empty()


async def ping_bilateral(req: AsyncIterator[Empty]) -> AsyncIterator[Empty]:
    yield Empty()


@dataclass
class Service(IService):
    name: str = field(default="service1")
    module: str = field(default="module1")
    package: str = ""
    options: Sequence[str] = field(default_factory=list[str])
    comments: str = ""
    _methods: Sequence["LabeledMethod"] = field(default_factory=list["LabeledMethod"])

    module_level_options: Iterable[str] = field(default_factory=list[str])
    module_level_comments: Iterable[str] = field(default_factory=list[str])

    @property
    def methods(self) -> Sequence["LabeledMethod"]:
        return self._methods

    @property
    def qual_name(self) -> str:
        if self.package:
            return f"{self.package}.{self.name}"
        return self.name


@dataclass
class LabeledMethod(ILabeledMethod):
    name: str = field(default="")
    method: Callable[..., Any] = field(default=lambda x: x)
    module: str = field(default="module1")
    service: str = field(default="service1")
    package: str = field(default="")
    options: Sequence[str] = field(default_factory=list[str])
    comments: str = field(default="")
    request_types: Sequence[Any] = field(default_factory=list[Any])
    response_types: Optional[Any] = None


@pytest.fixture
def simple_service() -> Service:
    service = Service(
        name="simple_service",
        comments="Simple Service",
        options=[],
        package="",
        module="protofile1",
        _methods=[],
    )

    unary_ping = LabeledMethod(
        name="ping",
        comments="Ping Method",
        options=[],
        request_types=[empty_instance],
        response_types=empty_instance,
        method=ping,
    )
    client_stream_ping = LabeledMethod(
        name="ping_client_stream",
        comments="Ping Method Client Stream",
        options=[],
        request_types=[empty_iterator],
        response_types=empty_instance,
        method=ping_client_stream,
    )
    server_stream_ping = LabeledMethod(
        name="server_stream_ping",
        comments="Ping Method Server Stream",
        options=[],
        request_types=[empty_instance],
        response_types=empty_iterator,
        method=ping_server_stream,
    )
    bilateral_ping = LabeledMethod(
        name="ping_bilateral",
        comments="Ping Method Bilateral",
        options=[],
        request_types=[empty_iterator],
        response_types=empty_iterator,
        method=ping_bilateral,
    )
    service._methods = [
        unary_ping,
        client_stream_ping,
        server_stream_ping,
        bilateral_ping,
    ]
    return service


def write_template(rendered: str, filename: str, expected_files: int) -> None:

    with TemporaryDirectory() as temp_dir:
        proto_path = Path(temp_dir).resolve()

        filename = f"{filename}.proto"
        with open(proto_path / filename, "w", encoding="utf-8") as f:
            f.write(rendered)

        output_dir = proto_path / "compiled"
        output_dir.mkdir(exist_ok=True)
        compile_protoc(
            root=proto_path,
            files=[filename],
            dst=output_dir,
            clss=True,
            services=True,
            mypy_stubs=False,
        )
        created_files = list(proto_path.rglob("*"))
        assert len(created_files) == expected_files
