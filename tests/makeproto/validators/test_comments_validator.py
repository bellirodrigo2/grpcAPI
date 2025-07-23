import pytest

from grpcAPI.makeproto.compiler import CompilerContext, list_ctx_error_code
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate
from grpcAPI.makeproto.validators.comment import CommentsValidator
from tests.makeproto.test_helpers import make_method, make_service


@pytest.fixture
def context() -> CompilerContext:
    return CompilerContext()


@pytest.fixture
def service() -> ServiceTemplate:
    return make_service("service1")


@pytest.fixture
def method(service: ServiceTemplate) -> MethodTemplate:
    return make_method("method1", service=service)


@pytest.fixture
def validator() -> CommentsValidator:
    return CommentsValidator()


# ---------- Testes ----------


def test_initial_context_empty(
    context: CompilerContext, service: ServiceTemplate
) -> None:
    report = context.get_report(service)
    assert len(context) == 0
    assert report is not None


def test_comments_ok(
    context: CompilerContext,
    service: ServiceTemplate,
    method: MethodTemplate,
    validator: CommentsValidator,
) -> None:
    comments = "foobar"
    service.comments = comments
    method.comments = comments
    validator.execute([service], context)
    assert len(context) == 0


def test_description_fail(
    context: CompilerContext,
    service: ServiceTemplate,
    method: MethodTemplate,
    validator: CommentsValidator,
) -> None:
    service.comments = "comments"
    method.comments = 3.45  # type: ignore
    validator.execute([service], context)
    assert len(context) == 1
    errors = list_ctx_error_code(context)
    assert all(err == "E401" for err in errors)


def test_description_2fails(
    context: CompilerContext,
    service: ServiceTemplate,
    method: MethodTemplate,
    validator: CommentsValidator,
) -> None:
    service.comments = []  # type: ignore
    method.comments = None
    validator.execute([service], context)
    assert len(context) == 2
    errors = list_ctx_error_code(context)
    assert all(err == "E401" for err in errors)
