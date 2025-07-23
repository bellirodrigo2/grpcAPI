import pytest

from grpcAPI.makeproto.compiler import CompilerContext, list_ctx_error_code
from grpcAPI.makeproto.report import CompileReport
from grpcAPI.makeproto.template import ServiceTemplate
from grpcAPI.makeproto.validators.name import (
    BlockNameValidator,
    FieldNameValidator,
    check_valid_filenames,
)
from tests.makeproto.test_helpers import make_method, make_service


@pytest.fixture
def block() -> ServiceTemplate:
    return make_service("ValidBlock")


@pytest.fixture
def block_name_validator() -> BlockNameValidator:
    return BlockNameValidator()


@pytest.fixture
def field_name_validator() -> FieldNameValidator:
    return FieldNameValidator()


@pytest.fixture
def context() -> CompilerContext:
    return CompilerContext()


# ---------- BlockNameValidator Tests ----------


def test_valid_block_name(
    block: ServiceTemplate,
    block_name_validator: BlockNameValidator,
    context: CompilerContext,
) -> None:
    block_name_validator.execute([block], context)
    assert len(context) == 0


def test_invalid_block_name(
    block_name_validator: BlockNameValidator, context: CompilerContext
) -> None:
    block = make_service("1InvalidName")
    block_name_validator.execute([block], context)
    report = context.get_report(block)
    assert len(context) == 1
    assert any(e.code == "E101" for e in report.errors)


def test_reserved_word_block_name(
    block_name_validator: BlockNameValidator, context: CompilerContext
) -> None:
    reserved_block = make_service("message")  # palavra reservada
    block_name_validator.execute([reserved_block], context)
    assert all(code == "E102" for code in list_ctx_error_code(context))


def test_non_duplicated_block_name(
    block: ServiceTemplate,
    block_name_validator: BlockNameValidator,
    context: CompilerContext,
) -> None:
    block1 = make_service("Other1")
    block2 = make_service("Other3")
    block_name_validator.execute([block, block1, block2], context)
    assert len(context) == 0


def test_duplicated_block_name(
    block: ServiceTemplate,
    block_name_validator: BlockNameValidator,
    context: CompilerContext,
) -> None:
    block1 = make_service("Other1")
    block2 = make_service("Other1")
    block_name_validator.execute([block, block1, block2], context)
    assert len(context) == 1
    assert all(code == "E104" for code in list_ctx_error_code(context))


def test_2duplicated_block_name(
    block: ServiceTemplate,
    block_name_validator: BlockNameValidator,
    context: CompilerContext,
) -> None:
    block1 = make_service("Other1")
    block2 = make_service("Other1")
    block3 = make_service("Other1")
    block_name_validator.execute([block, block1, block2, block3], context)
    assert len(context) == 2
    assert all(code == "E104" for code in list_ctx_error_code(context))


# ---------- FieldNameValidator Tests ----------


@pytest.fixture
def field_block() -> ServiceTemplate:
    return make_service("ValidBlock")


def test_valid_field_name(
    field_block: ServiceTemplate,
    field_name_validator: FieldNameValidator,
    context: CompilerContext,
) -> None:
    make_method(name="field1", service=field_block)
    field_name_validator.execute([field_block], context)
    assert len(context) == 0


def test_invalid_field_name(
    field_block: ServiceTemplate,
    field_name_validator: FieldNameValidator,
    context: CompilerContext,
) -> None:
    make_method("1InvalidName", service=field_block)
    make_method("", service=field_block)
    field_name_validator.execute([field_block], context)
    assert len(context) == 2
    assert all(code == "E101" for code in list_ctx_error_code(context))


def test_duplicated_field_name(
    field_block: ServiceTemplate,
    field_name_validator: FieldNameValidator,
    context: CompilerContext,
) -> None:
    make_method("field1", service=field_block)
    make_method("field1", service=field_block)
    make_method("field1", service=field_block)
    field_name_validator.execute([field_block], context)
    assert len(context) == 2
    assert all(code == "E104" for code in list_ctx_error_code(context))


def test_invalid_modules_name() -> None:

    invalid_names = ["valid", None, {"foo": "bar"}]

    report = CompileReport("Test", [])

    check_valid_filenames(invalid_names, report)
    assert len(report.errors) == 2
    assert [err.code for err in report.errors] == ["E101", "E101"]
