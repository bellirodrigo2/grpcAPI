from typing import Any, Dict

import pytest

from grpcAPI.makeproto.template import render_protofile_template


def normalize_proto(proto_str: str) -> str:
    return "\n".join(
        line.strip() for line in proto_str.strip().splitlines() if line.strip()
    )


@pytest.fixture
def simple_service() -> Dict[str, str]:
    return {
        "service_name": "simple",
        "service_comment": "// Simple Service",
        "methods": [
            {
                "name": "ping",
                "comment": "// Ping method",
                "request_type": "empty.Empty",
                "request_stream": False,
                "response_type": "empty.Empty",
                "response_stream": False,
                "options": [],
            }
        ],
    }


def test_protofile_basic(simple_service: Dict[str, str]) -> None:
    data = {
        "comment": "// This is a proto file",
        "syntax": "proto3",
        "package": "my.package",
        "imports": ["google/protobuf/empty.proto"],
        "services": [simple_service],
    }

    result = render_protofile_template(data)
    expected = """
    /* "Generated .proto file" */
    // This is a proto file
    syntax = "proto3";

    package my.package;

    import "google/protobuf/empty.proto";

    // Simple Service
    service simple {
      // Ping method
      rpc ping(empty.Empty) returns (empty.Empty);
    }
    """
    # print(result)
    assert normalize_proto(result) == normalize_proto(expected)


def test_protofile_no_services():
    data = {
        "comment": "// No services here",
        "syntax": "proto3",
        "package": "empty.package",
        "imports": [],
        "services": [],
    }

    result = render_protofile_template(data)
    expected = """
    /* "Generated .proto file" */
    // No services here
    syntax = "proto3";

    package empty.package;
    """
    assert normalize_proto(result) == normalize_proto(expected)


@pytest.fixture
def service_with_options() -> Dict[str, Any]:
    return {
        "service_name": "user",
        "service_comment": "// User-related operations",
        "methods": [
            {
                "name": "createUser",
                "comment": "// Creates a user",
                "request_type": "user.UserInput",
                "request_stream": False,
                "response_type": "user.User",
                "response_stream": False,
                "options": ["deprecated = false"],
            }
        ],
    }


@pytest.fixture
def streaming_service() -> Dict[str, Any]:
    return {
        "service_name": "stream",
        "service_comment": "// Streaming API",
        "methods": [
            {
                "name": "watchEvents",
                "comment": "// Watches events",
                "request_type": "event.EventRequest",
                "request_stream": False,
                "response_type": "event.Event",
                "response_stream": True,
                "options": [],
            }
        ],
    }


def test_protofile_multiple_services(service_with_options, streaming_service):
    data = {
        "comment": "// Multi-service protofile",
        "syntax": "proto3",
        "package": "multi.services",
        "imports": ["user.proto", "event.proto"],
        "services": [service_with_options, streaming_service],
    }

    result = render_protofile_template(data)
    expected = """
    /* "Generated .proto file" */
    // Multi-service protofile
    syntax = "proto3";

    package multi.services;

    import "user.proto";
    import "event.proto";

    // User-related operations
    service user {
      // Creates a user
      rpc createUser(user.UserInput) returns (user.User){
        option deprecated = false;
      };
    }

    // Streaming API
    service stream {
      // Watches events
      rpc watchEvents(event.EventRequest) returns (stream event.Event);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_protofile_with_global_options(simple_service: Dict[str, str]) -> None:
    data = {
        "comment": "// Proto with global options",
        "syntax": "proto3",
        "package": "opt.global",
        "imports": [],
        "services": [simple_service],
        "options": ['java_package = "com.example.proto"', "optimize_for = SPEED"],
    }

    result = render_protofile_template(data)
    expected = """
    /* "Generated .proto file" */
    // Proto with global options
    syntax = "proto3";

    package opt.global;

    option java_package = "com.example.proto";
    option optimize_for = SPEED;

    // Simple Service
    service simple {
      // Ping method
      rpc ping(empty.Empty) returns (empty.Empty);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_protofile_missing_package(simple_service: Dict[str, str]) -> None:
    data = {
        "comment": "// No package defined",
        "syntax": "proto3",
        "package": "",
        "imports": [],
        "services": [simple_service],
    }

    result = render_protofile_template(data)
    expected = """
    /* "Generated .proto file" */
    // No package defined
    syntax = "proto3";

    // Simple Service
    service simple {
      // Ping method
      rpc ping(empty.Empty) returns (empty.Empty);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_protofile_missing_comment(simple_service: Dict[str, str]) -> None:
    data = {
        "comment": "",
        "syntax": "proto3",
        "package": "no.comment",
        "imports": [],
        "services": [simple_service],
    }

    result = render_protofile_template(data)
    expected = """
    /* "Generated .proto file" */
    syntax = "proto3";

    package no.comment;

    // Simple Service
    service simple {
      // Ping method
      rpc ping(empty.Empty) returns (empty.Empty);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)
