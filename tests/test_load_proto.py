import shutil
from pathlib import Path
from types import ModuleType
from typing import List

from grpcAPI.adaptors.grpcio_impl import GrpcioServiceModule
from grpcAPI.app import BaseService
from grpcAPI.interface import IServiceModule
from grpcAPI.proto_build import pack_protos
from grpcAPI.proto_load import load_proto
from tests.conftest import root


def test_load_basic(basic_proto: BaseService, temp_dir: Path) -> None:

    services = {"": [basic_proto]}
    shutil.copytree(root, temp_dir, dirs_exist_ok=True)

    pack = pack_protos(services=services, root_dir=root, out_dir=temp_dir)

    lib_path = temp_dir / "lib"
    lib_path.mkdir(parents=True, exist_ok=True)
    modules_dict = load_proto(
        root_dir=temp_dir,
        files=list(pack),
        dst=lib_path,
        logger=None,
        module_factory=GrpcioServiceModule,
    )

    packages = list(modules_dict.keys())
    assert packages == [""]
    no_package = modules_dict[""]
    assert list(no_package.keys()) == ["service"]


def test_load_clean_up(
    basic_proto: BaseService,
) -> None:
    services = {"": [basic_proto]}
    pack = pack_protos(services=services, root_dir=root)
    lib_path = root.parent / "lib"
    modules_dict = load_proto(
        root_dir=root,
        files=list(pack),
        dst=lib_path,
        logger=None,
        clean_services=True,
        module_factory=GrpcioServiceModule,
    )
    assert list(modules_dict.keys()) == [""]
    no_package = modules_dict[""]
    assert list(no_package.keys()) == ["service"]
    assert isinstance(no_package["service"], IServiceModule)


def test_load_complex(complex_proto: List[BaseService], temp_dir: Path) -> None:

    service1, service2, service3 = complex_proto
    services = {"": [service1, service2], "pack3": [service3]}

    shutil.copytree(root, temp_dir, dirs_exist_ok=True)

    pack = pack_protos(services=services, root_dir=root, out_dir=temp_dir)

    lib_path = temp_dir / "lib"
    lib_path.mkdir(parents=True, exist_ok=True)
    modules_dict = load_proto(
        temp_dir, list(pack), lib_path, None, module_factory=GrpcioServiceModule
    )

    packages = list(modules_dict.keys())
    assert sorted(packages) == sorted(["", "pack3"])
    no_package = modules_dict[""]
    assert list(no_package.keys()) == ["service"]
    pack3 = modules_dict["pack3"]
    assert list(pack3.keys()) == ["mod3"]


def test_load_overwrite(basic_proto: BaseService) -> None:
    pass


def test_load_all_services() -> None:
    pass
