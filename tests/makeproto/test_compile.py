from typing import List

import pytest

from grpcAPI.makeproto.build_service import (
    CompilationError,
    make_setters,
    make_validators,
)
from grpcAPI.makeproto.compiler import CompilerContext, CompilerPass
from grpcAPI.makeproto.compiler_passes import run_compiler_passes
from grpcAPI.makeproto.format_comment import format_comment
from grpcAPI.makeproto.make_service_template import make_service_template
from grpcAPI.makeproto.template import (
    ProtoTemplate,
    ServiceTemplate,
    render_protofile_template,
)
from tests.conftest import Service, write_template


@pytest.fixture
def simple_prototemplate() -> ProtoTemplate:
    protofile_name = "protofile1"

    return ProtoTemplate(
        comments="Proto File for testing",
        package="my.package",
        module=protofile_name,
        syntax=3,
        imports=set(),
        services=[],
        options=[],
    )


@pytest.fixture
def compiler_pass() -> List[List[CompilerPass]]:
    validators = make_validators()
    setters = make_setters(format_comment=lambda x: format_comment(x, False))
    return [validators, setters]


def build_proto(
    ctx: CompilerContext,
    blocks: List[ServiceTemplate],
    compilerpasses: List[List[CompilerPass]],
) -> None:
    for compilerpass in compilerpasses:
        run_compiler_passes([(blocks, ctx)], compilerpass)


def test_protofile_basic(
    simple_service: Service,
    simple_prototemplate: ProtoTemplate,
    compiler_pass: List[List[CompilerPass]],
) -> None:
    protofile = simple_prototemplate
    ctx = CompilerContext(state={protofile.module: protofile})

    no_method = ServiceTemplate(
        name="empty_service",
        comments="Empty Service",
        options=[],
        package="",
        module="protofile1",
        methods=[],
    )
    simple_service_template = make_service_template(simple_service)
    blocks = [simple_service_template, no_method]

    build_proto(ctx, blocks, compiler_pass)

    protofile_dict = protofile.to_dict()
    rendered = render_protofile_template(protofile_dict)
    write_template(rendered, protofile.module, 4)


def test_protofile_empty(
    simple_prototemplate: ProtoTemplate,
) -> None:
    protofile = simple_prototemplate
    protofile_dict = protofile.to_dict()

    rendered = render_protofile_template(protofile_dict)
    assert rendered == ""


def test_failure_service(
    simple_prototemplate: ProtoTemplate,
    compiler_pass: List[List[CompilerPass]],
) -> None:
    protofile = simple_prototemplate
    ctx = CompilerContext(state={protofile.module: protofile})

    failed_service = ServiceTemplate(
        name="This Name is invalid",
        comments="Empty Service",
        options=[],
        package="",
        module="protofile1",
        methods=[],
    )
    blocks = [failed_service]

    with pytest.raises(CompilationError):
        build_proto(ctx, blocks, compiler_pass)
