import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Generator, List

import pytest
from makeproto import IService, compile_service

from grpcAPI.adaptors.impl import label_method
from grpcAPI.app import BaseService
from grpcAPI.protoc_compile import compile_protoc

# Add 'tests/lib' to sys.path for import resolution
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path.resolve()))
from google.protobuf.descriptor_pb2 import DescriptorProto
from google.protobuf.timestamp_pb2 import Timestamp

from tests.lib.other_pb2 import Other
from tests.lib.user_pb2 import User


def assert_createds(temp_dir: Path, expected_num: int, print_: bool = False) -> None:
    lib_dir = temp_dir / "lib"
    assert lib_dir.exists(), "'lib' directory was not created"
    assert lib_dir.is_dir(), "'lib' is not a directory"

    py_files = list(lib_dir.rglob("*.py*"))  # recursive
    assert py_files, "No .py files were generated"
    assert len(py_files) == expected_num
    if print_:
        for file in py_files:
            print(file)


def write_proto(temp_dir: Path, protofile_str: str, filename: str) -> None:
    assert temp_dir.exists()
    assert any(temp_dir.iterdir())

    service_path = temp_dir / "proto" / "service"
    service_path.mkdir(parents=True, exist_ok=True)

    with open(service_path / filename, "w") as file:
        file.write(protofile_str)


def assert_content(protofile_str: str, content: List[str]) -> None:
    for line in content:
        assert line in protofile_str


def compile_and_write_protos(
    services: Dict[str, List[IService]], dst_dir: Path
) -> None:
    protodict = defaultdict(dict)
    proto_stream = compile_service(services)

    if proto_stream:
        for proto in proto_stream:
            protodict[proto.package][proto.filename] = proto.content

    for package, file_dict in protodict.items():
        for filename, proto_str in file_dict.items():
            print(filename)
            write_proto(dst_dir, proto_str, f"{filename}.proto")


def compile_write_protoc_assert(
    services: Dict[str, List[IService]], temp_dir: Path, expected_files: int
) -> None:
    compile_and_write_protos(services, temp_dir)
    compile_protoc(temp_dir, "proto", "lib", False, True, False)
    assert_createds(temp_dir, expected_files)


@pytest.fixture
def serviceapi() -> BaseService:
    return BaseService(name="service1", label_method=label_method)


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

    serviceapi2 = BaseService(name="service2", label_method=label_method)

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
        name="service3", package="pack3", module="mod3", label_method=label_method
    )

    @serviceapi3
    async def unary(req: User) -> DescriptorProto:
        pass

    @serviceapi3
    async def clientstream(req: AsyncIterator[DescriptorProto]) -> Other:
        pass

    return [basic_proto, serviceapi2, serviceapi3]


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
