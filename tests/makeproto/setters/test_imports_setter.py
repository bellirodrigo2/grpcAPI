import pytest
from typing_extensions import Any

from grpcAPI.makeproto.compiler import CompilerContext
from grpcAPI.makeproto.setters.imports import ImportsSetter
from grpcAPI.makeproto.template import ProtoTemplate, ServiceTemplate
from tests.makeproto.test_helpers import make_method, make_service


class Mock1:
    proto_path: str = "objects/user.proto"


@pytest.fixture
def context_and_template() -> tuple[CompilerContext, ProtoTemplate, ServiceTemplate]:
    mod = "module1"
    block = make_service(name="TestBlock", module=mod)
    template = ProtoTemplate(
        comments="",
        syntax=3,
        package="pack1",
        module="module1",
        imports=set(),
        services=[],
        options=[],
    )
    context = CompilerContext(state={mod: template})
    return context, template, block


def test_imports_setter_ok(
    context_and_template: tuple[CompilerContext, ProtoTemplate, Any],
) -> None:
    context, template, block = context_and_template

    make_method(
        name="method1",
        requests=[Mock1],
        response=Mock1,
        service=block,
    )

    import_setter = ImportsSetter()
    import_setter.execute([block], context)

    assert template.imports == {"objects/user.proto"}


def test_imports_setter_no_prototemplate(
    context_and_template: tuple[CompilerContext, ProtoTemplate, Any],
) -> None:
    _, template, block = context_and_template
    context = CompilerContext()

    make_method(
        name="method1",
        requests=[Mock1],
        response=Mock1,
        service=block,
    )

    import_setter = ImportsSetter()
    import_setter.execute([block], context)

    assert template.imports == set()
    assert len(context) == 1
