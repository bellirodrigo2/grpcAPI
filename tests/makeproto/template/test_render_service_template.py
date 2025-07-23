from grpcAPI.makeproto.template import (
    render_protofile_template,
    render_service_template,
)


def normalize_proto(s: str) -> str:
    return "\n".join(line.strip() for line in s.strip().splitlines())


def test_basic_service_with_options() -> None:
    result = render_service_template(
        {
            "service_name": "user_service",
            "service_comment": "// User Service APIs",
            "methods": [
                {
                    "name": "newuser",
                    "comment": "// Create a new user",
                    "request_type": "userpack.UserInput",
                    "request_stream": False,
                    "response_type": "userpack.User",
                    "response_stream": False,
                    "options": ["deprecated = false"],
                }
            ],
        }
    )

    expected = """
    // User Service APIs
    service user_service {
      // Create a new user
      rpc newuser(userpack.UserInput) returns (userpack.User){
        option deprecated = false;
      };
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_service_with_streams_and_no_options() -> None:
    result = render_service_template(
        {
            "service_name": "stream_service",
            "service_comment": "// Handles streaming",
            "methods": [
                {
                    "name": "upload",
                    "comment": "// Stream upload",
                    "request_type": "mypack.DataChunk",
                    "request_stream": True,
                    "response_type": "mypack.UploadAck",
                    "response_stream": False,
                    "options": [],
                },
                {
                    "name": "watch",
                    "comment": "// Watch stream",
                    "request_type": "mypack.Request",
                    "request_stream": False,
                    "response_type": "mypack.Event",
                    "response_stream": True,
                    "options": [],
                },
            ],
        }
    )

    expected = """
    // Handles streaming
    service stream_service {
      // Stream upload
      rpc upload(stream mypack.DataChunk) returns (mypack.UploadAck);
      // Watch stream
      rpc watch(mypack.Request) returns (stream mypack.Event);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_multiple_options() -> None:
    result = render_service_template(
        {
            "service_name": "multi_option",
            "service_comment": "// Multi-option test",
            "methods": [
                {
                    "name": "complex",
                    "comment": "// Method with multiple options",
                    "request_type": "data.Req",
                    "request_stream": False,
                    "response_type": "data.Res",
                    "response_stream": False,
                    "options": ["deprecated = false", "idempotency_level = IDEMPOTENT"],
                }
            ],
        }
    )

    expected = """
    // Multi-option test
    service multi_option {
      // Method with multiple options
      rpc complex(data.Req) returns (data.Res){
        option deprecated = false;
        option idempotency_level = IDEMPOTENT;
      };
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_service_with_no_methods() -> None:
    result = render_service_template(
        {
            "service_name": "empty_service",
            "service_comment": "// No methods here",
            "methods": [],
        }
    )

    expected = """
    // No methods here
    service empty_service {
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_service_with_missing_comments() -> None:
    result = render_service_template(
        {
            "service_name": "no_comments",
            "service_comment": "",
            "methods": [
                {
                    "name": "ping",
                    "comment": "",
                    "request_type": "google.protobuf.Empty",
                    "request_stream": False,
                    "response_type": "google.protobuf.Empty",
                    "response_stream": False,
                    "options": [],
                }
            ],
        }
    )

    expected = """
    service no_comments {
      rpc ping(google.protobuf.Empty) returns (google.protobuf.Empty);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_bidirectional_streaming() -> None:
    result = render_service_template(
        {
            "service_name": "chat_service",
            "service_comment": "// Bi-directional streaming chat",
            "methods": [
                {
                    "name": "chat",
                    "comment": "// Chat stream",
                    "request_type": "chat.Message",
                    "request_stream": True,
                    "response_type": "chat.Message",
                    "response_stream": True,
                    "options": [],
                }
            ],
        }
    )

    expected = """
    // Bi-directional streaming chat
    service chat_service {
      // Chat stream
      rpc chat(stream chat.Message) returns (stream chat.Message);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_weird_characters_in_names() -> None:
    result = render_service_template(
        {
            "service_name": "Service_123$",
            "service_comment": "// Unusual service name",
            "methods": [
                {
                    "name": "do_Stuff99$",
                    "comment": "// Weird method",
                    "request_type": "weird.Type",
                    "request_stream": False,
                    "response_type": "weird.Response",
                    "response_stream": False,
                    "options": [],
                }
            ],
        }
    )

    expected = """
    // Unusual service name
    service Service_123$ {
      // Weird method
      rpc do_Stuff99$(weird.Type) returns (weird.Response);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_method_with_none_options() -> None:
    result = render_service_template(
        {
            "service_name": "null_options",
            "service_comment": "// Null options test",
            "methods": [
                {
                    "name": "noop",
                    "comment": "// Does nothing",
                    "request_type": "google.protobuf.Empty",
                    "request_stream": False,
                    "response_type": "google.protobuf.Empty",
                    "response_stream": False,
                    "options": None,
                }
            ],
        }
    )

    expected = """
    // Null options test
    service null_options {
      // Does nothing
      rpc noop(google.protobuf.Empty) returns (google.protobuf.Empty);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_duplicate_methods() -> None:
    result = render_service_template(
        {
            "service_name": "dup_service",
            "service_comment": "// Duplicate methods (still legal)",
            "methods": [
                {
                    "name": "echo",
                    "comment": "// First echo",
                    "request_type": "msg.Input",
                    "request_stream": False,
                    "response_type": "msg.Output",
                    "response_stream": False,
                    "options": [],
                },
                {
                    "name": "echo",
                    "comment": "// Second echo",
                    "request_type": "msg.Input",
                    "request_stream": False,
                    "response_type": "msg.Output",
                    "response_stream": False,
                    "options": [],
                },
            ],
        }
    )

    expected = """
    // Duplicate methods (still legal)
    service dup_service {
      // First echo
      rpc echo(msg.Input) returns (msg.Output);
      // Second echo
      rpc echo(msg.Input) returns (msg.Output);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_deeply_nested_types() -> None:
    result = render_service_template(
        {
            "service_name": "nested_types",
            "service_comment": "// Uses nested request/response types",
            "methods": [
                {
                    "name": "analyze",
                    "comment": "// Analyze deeply",
                    "request_type": "pkg.alpha.beta.Request",
                    "request_stream": False,
                    "response_type": "pkg.alpha.beta.Response",
                    "response_stream": False,
                    "options": [],
                }
            ],
        }
    )

    expected = """
    // Uses nested request/response types
    service nested_types {
      // Analyze deeply
      rpc analyze(pkg.alpha.beta.Request) returns (pkg.alpha.beta.Response);
    }
    """
    assert normalize_proto(result) == normalize_proto(expected)


def test_empty_proto() -> None:
    result = render_protofile_template({})
    assert result == ""
