import pytest

from grpcAPI.makeproto.build_service import compile_service
from tests.conftest import Service, write_template


def test_protofile_basic(
    simple_service: Service,
) -> None:
    comment1 = "This a file comment from simple service"
    comment2 = "This a file comment from service2"
    opt1 = 'java_package = "com.makeproto"'
    opt2 = 'go_package = "makeproto.go.package"'
    opt3 = "java_multiple_files = true"

    simple_service.module_level_comments = [comment1]
    simple_service.module_level_options = [opt1, opt3]
    service2 = Service(
        name="service_2",
        comments="Service2",
        module="protofile1",
        module_level_options=[opt2, opt3],
        module_level_comments=[comment2],
    )
    proto_list = list(compile_service({"": [simple_service, service2]}))
    assert len(proto_list) == 1
    proto_package = proto_list[0]
    rendered = proto_package.content
    assert comment1 in rendered
    assert comment2 in rendered
    assert opt1 in rendered
    assert opt2 in rendered
    assert opt3 in rendered
    write_template(rendered, proto_package.filename, 4)


def test_empty() -> None:
    compile_service({"empty": []})


def test_invalid_package_name(
    simple_service: Service, capfd: pytest.CaptureFixture[str]
) -> None:
    pack1 = "pack1"
    service = Service(name="invalid name", package=pack1)
    pack2 = "pack2"
    service2 = Service(name="serv", package=pack2)
    service3 = Service(name="serv", package=pack2)

    compile_service(
        {"": [simple_service], pack1: [service], pack2: [service2, service3]}
    )

    out, err = capfd.readouterr()
    assert "Invalid name" in out
    assert "Duplicated name: Duplicated Service name" in out
