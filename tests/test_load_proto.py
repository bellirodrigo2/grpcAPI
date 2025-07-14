import shutil
from pathlib import Path
from typing import List

from grpcAPI.app import APIService
from grpcAPI.interfaces import ServiceModule
from grpcAPI.proto_build import pack_protos
from grpcAPI.proto_load import load_proto
from tests.conftest import root


def test_load_basic(basic_proto: APIService, temp_dir: Path) -> None:

    services = {"": [basic_proto]}
    shutil.copytree(root, temp_dir, dirs_exist_ok=True)

    pack = pack_protos(services=services, root_dir=root, out_dir=temp_dir, type_cast=[])

    lib_path = temp_dir / "lib"
    lib_path.mkdir(parents=True, exist_ok=True)
    modules_dict = load_proto(
        root_dir=temp_dir,
        files=list(pack),
        dst=lib_path,
    )

    packages = list(modules_dict.keys())
    assert packages == [""]
    no_package = modules_dict[""]
    assert list(no_package.keys()) == ["service"]


def test_load_clean_up(
    basic_proto: APIService,
) -> None:
    services = {"": [basic_proto]}
    pack = pack_protos(services=services, root_dir=root, type_cast=[])
    lib_path = root.parent / "lib"
    modules_dict = load_proto(
        root_dir=root,
        files=list(pack),
        dst=lib_path,
        clean_services=True,
    )
    assert list(modules_dict.keys()) == [""]
    no_package = modules_dict[""]
    assert list(no_package.keys()) == ["service"]
    assert isinstance(no_package["service"], ServiceModule)


def test_load_complex(complex_proto: List[APIService], temp_dir: Path) -> None:

    service1, service2, service3 = complex_proto
    services = {"": [service1, service2], "pack3": [service3]}

    shutil.copytree(root, temp_dir, dirs_exist_ok=True)

    pack = pack_protos(services=services, root_dir=root, out_dir=temp_dir, type_cast=[])

    lib_path = temp_dir / "lib"
    lib_path.mkdir(parents=True, exist_ok=True)
    modules_dict = load_proto(
        temp_dir,
        list(pack),
        lib_path,
    )

    packages = list(modules_dict.keys())
    assert sorted(packages) == sorted(["", "pack3"])
    no_package = modules_dict[""]
    assert list(no_package.keys()) == ["service"]
    pack3 = modules_dict["pack3"]
    assert list(pack3.keys()) == ["mod3"]


def test_load_overwrite(basic_proto: APIService) -> None:
    pass


def test_load_all_services() -> None:
    pass
