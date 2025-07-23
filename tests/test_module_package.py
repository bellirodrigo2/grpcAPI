import pytest

from grpcAPI.app import APIService
from grpcAPI.package_module import (  # ajuste o import real
    APIModule,
    APIPackage,
    MetaData,
)


def test_metadata_basic() -> None:
    meta = MetaData(name="core", options=["opt1", "opt2"], comments=["c1", "c2"])
    assert meta.name == "core"
    assert meta.options == ["opt1", "opt2"]
    assert meta.comments == ["c1", "c2"]


def test_apipackage_make_module() -> None:
    pkg = APIPackage(name="pkg", options=["opt"], comments=["comment"])
    module = pkg.make_module("mod1")

    assert isinstance(module, APIModule)
    assert module.name == "mod1"
    assert module.package == "pkg"
    assert module.options == ["opt"]
    assert module.comments == ["comment"]


def test_apimodule_make_service_full_args() -> None:
    mod = APIModule(name="mod", package="pkg", options=["opt1"], comments=["c1"])

    service = mod.make_service(
        service_name="svc",
        options=["svc_opt"],
        comments="svc comment",
        title="Test Title",
        description="Test Desc",
        tags=["tag1", "tag2"],
    )

    assert isinstance(service, APIService)
    assert service.name == "svc"
    assert service.module == "mod"
    assert service.package == "pkg"
    assert service.module_level_options == ["opt1"]
    assert service.module_level_comments == ["c1"]
    assert service.options == ["svc_opt"]
    assert service.comments == "svc comment"
    assert service.title == "Test Title"
    assert service.description == "Test Desc"
    assert service.tags == ["tag1", "tag2"]


def test_apimodule_make_service_defaults() -> None:
    mod = APIModule(name="mod", package="pkg", options=[], comments=[])
    servname = "svc"
    service = mod.make_service(service_name=servname)

    assert service.name == "svc"
    assert service.module == "mod"
    assert service.package == "pkg"
    assert service.options == []
    assert service.comments == ""
    assert service.title == servname
    assert service.description == ""
    assert service.tags == []
