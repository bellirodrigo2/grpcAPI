from typing import Any, List, Mapping, Optional, Type

import pytest

from grpcAPI.makeproto import ILabeledMethod
from grpcAPI.process_service.format_service import (
    FormatService,
    FormatServiceFactory,
    format_multiline,
)


class FakeBase:
    def __init__(
        self,
        name: str,
        title: str,
        description: str,
        tags: List[str],
        comments: str = "",
        request_types: Optional[List[Type[Any]]] = None,
        response_types: Optional[Type[Any]] = None,
    ) -> None:
        self.name = name
        self.title = title
        self.description = description
        self.tags = tags
        self.comments = comments


class FakeMethod(FakeBase):
    def __init__(
        self,
        name: str,
        title: str,
        description: str,
        tags: List[str],
        comments: str = "",
        request_types: Optional[List[Type[Any]]] = None,
        response_types: Optional[Type[Any]] = None,
    ) -> None:
        super().__init__(
            name, title, description, tags, comments, request_types, response_types
        )
        self.request_types = request_types or []
        self.response_types = response_types


class FakeService(FakeBase):
    def __init__(
        self,
        name: str,
        title: str,
        description: str,
        tags: List[str],
        comments: str = "",
        methods: Optional[List[ILabeledMethod]] = None,
    ) -> None:
        super().__init__(name, title, description, tags, comments)
        self.methods = methods or []


@pytest.mark.parametrize(
    "strategy,expected_start",
    [
        ("singleline", "//Title:"),
        ("multiline", "/*"),
    ],
)
def test_comment_formatting_styles(strategy: str, expected_start: str) -> None:
    service = FakeService(
        name="MyService",
        title="My Title",
        description="Service description",
        tags=["x"],
        comments="This is a test service",
        methods=[
            FakeMethod(
                "CreateUser",
                "Create a user",
                "Creates users in db",
                ["user"],
                comments="method doc",
                request_types=["User"],
                response_types=["UserCreated"],
            )
        ],
    )

    format_service = FormatService(
        max_char=80,
        case="snake",
        strategy=strategy,
    )
    format_service(service)

    assert expected_start in service.comments
    assert "create_user" in service.methods[0].name


def test_title_case_conversion() -> None:
    service = FakeService(
        name="MyServiceTest",
        title="",
        description="",
        tags=[],
        methods=[
            FakeMethod("CreateAccount", "Create", "desc", ["a"]),
            FakeMethod("deleteUser", "Delete", "desc", ["b"]),
        ],
    )
    format_service = FormatService(80, case="pascal", strategy="singleline")
    format_service(service)

    assert service.name == "MyServiceTest"  # unchanged since it is already PascalCase
    assert service.methods[0].name == "CreateAccount"
    assert service.methods[1].name == "DeleteUser"

    format_service = FormatService(80, case="snake", strategy="singleline")
    format_service(service)
    assert service.methods[0].name == "create_account"
    assert service.methods[1].name == "delete_user"


def test_multiline_formatting_output() -> None:
    text = "This is a sample comment block that should be split across multiple lines if it exceeds the maximum character limit."
    result = format_multiline(text, max_char=50, start_char="*", end_char="*")
    lines = result.split("\n")

    for line in lines:
        assert line.startswith("*")
        assert line.endswith("*")
        assert len(line) == 50


def test_factory_default_values() -> None:
    factory = FormatServiceFactory()

    # no config provided
    settings: Mapping[str, Any] = {}
    service = factory(settings)
    assert isinstance(service, FormatService)
    assert service.max_char == 80
    assert service.case == "none"
    assert service.open_char.startswith("/*")

    # partial config
    settings = {"format": {"max_char_per_line": 100, "comment_style": "singleline"}}
    service = factory(settings)
    assert service.max_char == 100
    assert service.open_char == ""
    assert service.start_char == "//"
