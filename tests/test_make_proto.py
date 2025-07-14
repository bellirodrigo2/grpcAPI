from typing import List

import pytest

from grpcAPI.app import APIService
from grpcAPI.proto_build import compile_service, pack_protos
from tests.conftest import assert_content, root


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
    proto_stream = compile_service({"pack1": [basic_proto]})
    for proto in proto_stream:
        assert_content(proto.content, contents)


def test_basic(basic_proto: APIService) -> None:

    services = {"": [basic_proto]}
    pack = pack_protos(services=services, root_dir=root, type_cast=[])
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


def test_basic_overwirte(basic_proto: APIService) -> None:

    services = {"": [basic_proto]}
    pack_protos(services=services, root_dir=root, type_cast=[])
    with pytest.raises(FileExistsError):
        pack_protos(services=services, root_dir=root, overwrite=False, type_cast=[])


def test_complex(complex_proto: List[APIService]) -> None:

    service1, service2, service3 = complex_proto

    services = {"": [service1, service2], "pack3": [service3]}

    pack = pack_protos(services=services, root_dir=root, type_cast=[])
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
    pack = pack_protos(
        services=services,
        root_dir=root,
        type_cast=[],
        # custompassmethod=validate_signature_pass
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
