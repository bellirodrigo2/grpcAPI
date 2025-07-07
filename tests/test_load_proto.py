from pathlib import Path
from typing import List

from grpcAPI.app import BaseService
from grpcAPI.proto_build import pack_protos
from grpcAPI.proto_load import load_proto


def test_load_basic(basic_proto: BaseService, temp_dir: Path) -> None:

    services = {"": [basic_proto]}

    pack = pack_protos(
        services=services, root_dir=Path("./tests/proto"), out_dir=temp_dir
    )
    lib_path = temp_dir / "lib"
    lib_path.mkdir(parents=True, exist_ok=True)
    modules_dict = load_proto(temp_dir, list(pack), lib_path, None)
    packages = list(modules_dict.keys())
    assert packages == [""]
    no_package = modules_dict[""]
    assert list(no_package.keys()) == ["service"]


def test_load_complex(complex_proto: List[BaseService], temp_dir: Path) -> None:

    service1, service2, service3 = complex_proto

    services = {"": [service1, service2], "pack3": [service3]}

    pack = pack_protos(
        services=services, root_dir=Path("./tests/proto"), out_dir=temp_dir
    )

    lib_path = temp_dir / "lib"
    lib_path.mkdir(parents=True, exist_ok=True)
    modules_dict = load_proto(temp_dir, list(pack), lib_path, None)
    packages = list(modules_dict.keys())
    assert packages == ["", "pack3"]
    no_package = modules_dict[""]
    assert list(no_package.keys()) == ["service"]
    pack3 = modules_dict["pack3"]
    assert list(pack3.keys()) == ["mod3"]
