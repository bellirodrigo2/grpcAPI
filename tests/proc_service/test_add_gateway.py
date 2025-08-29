from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

import pytest

from grpcAPI.process_service.add_gateway import AddGateway, proto_http_option


@dataclass
class MockMethod:
    name: str = "test_method"
    meta: Dict[str, Any] = field(default_factory=dict)
    options: List[str] = field(default_factory=list)


@dataclass
class MockService:
    name: str = "TestService"
    module_level_imports: List[str] = field(default_factory=list)


class TestProtoHttpOption:

    def test_simple_get_request(self):
        """Test simple GET request formatting"""
        mapping = {"get": "/api/users"}
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/users"
  }"""
        assert result == expected

    def test_post_with_body(self):
        """Test POST request with body"""
        mapping = {"post": "/api/users", "body": "*"}
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    post: "/api/users"
    body: "*"
  }"""
        assert result == expected

    def test_path_parameters(self):
        """Test path parameters in URL"""
        mapping = {
            "get": "/api/users/{user_id}",
            "additional_bindings": [{"get": "/api/v1/users/{user_id}"}],
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/users/{user_id}"
    additional_bindings: [ { get: "/api/v1/users/{user_id}" } ]
  }"""
        assert result == expected

    def test_patch_with_field_mask(self):
        """Test PATCH request with field mask"""
        mapping = {
            "patch": "/api/users/{user_id}",
            "body": "*",
            "response_body": "user",
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    patch: "/api/users/{user_id}"
    body: "*"
    response_body: "user"
  }"""
        assert result == expected

    def test_delete_request(self):
        """Test DELETE request"""
        mapping = {"delete": "/api/users/{user_id}"}
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    delete: "/api/users/{user_id}"
  }"""
        assert result == expected

    def test_boolean_values(self):
        """Test boolean value formatting"""
        mapping = {"get": "/api/test", "deprecated": True, "internal": False}
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/test"
    deprecated: true
    internal: false
  }"""
        assert result == expected

    def test_numeric_values(self):
        """Test numeric value formatting"""
        mapping = {"get": "/api/test", "timeout": 30, "rate_limit": 100.5}
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/test"
    timeout: 30
    rate_limit: 100.5
  }"""
        assert result == expected

    def test_nested_objects(self):
        """Test nested object formatting"""
        mapping = {
            "post": "/api/users",
            "body": "user",
            "custom": {"auth": "required", "cache": 300},
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    post: "/api/users"
    body: "user"
    custom: { auth: "required" cache: 300 }
  }"""
        assert result == expected

    def test_array_values(self):
        """Test array value formatting"""
        mapping = {
            "get": "/api/test",
            "tags": ["public", "v1"],
            "methods": ["GET", "POST"],
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/test"
    tags: [ "public", "v1" ]
    methods: [ "GET", "POST" ]
  }"""
        assert result == expected

    def test_complex_additional_bindings(self):
        """Test complex additional bindings structure"""
        mapping = {
            "get": "/api/users/{user_id}",
            "additional_bindings": [
                {"get": "/api/v1/users/{user_id}"},
                {"post": "/api/users/{user_id}/refresh", "body": "*"},
            ],
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/users/{user_id}"
    additional_bindings: [ { get: "/api/v1/users/{user_id}" }, { post: "/api/users/{user_id}/refresh" body: "*" } ]
  }"""
        assert result == expected

    def test_unsupported_type_raises_error(self):
        """Test that unsupported types raise ValueError"""
        mapping = {"get": "/api/test", "unsupported": object()}  # Unsupported type

        with pytest.raises(ValueError, match="Unsupported type for value"):
            proto_http_option(mapping)


class TestAddGateway:

    def test_init(self):
        """Test AddGateway initialization"""
        gateway = AddGateway()
        assert gateway.word == "gateway"
        assert gateway.errors == {}
        assert gateway.current_service is None

    def test_process_service_sets_current_service(self):
        """Test that _process_service sets current service"""
        gateway = AddGateway()
        service = MockService(name="TestService")

        gateway._process_service(service)

        assert gateway.current_service is service

    def test_process_method_without_service_raises_error(self):
        """Test processing method without setting service first raises error"""
        gateway = AddGateway()
        method = MockMethod(name="test_method", meta={"gateway": {"get": "/api/test"}})

        # Don't call _process_service first
        with pytest.raises(ValueError, match="Current service is not set"):
            gateway._process_method(method)

    def test_process_method_without_gateway_meta(self):
        """Test processing method without gateway metadata"""
        gateway = AddGateway()
        service = MockService()
        method = MockMethod(name="test_method")

        gateway._process_service(service)
        gateway._process_method(method)

        assert len(method.options) == 0
        assert len(gateway.errors) == 0
        assert len(service.module_level_imports) == 0

    def test_process_method_with_gateway_meta(self):
        """Test processing method with gateway metadata"""
        gateway = AddGateway()
        service = MockService()
        method = MockMethod(
            name="get_user", meta={"gateway": {"get": "/api/users/{user_id}"}}
        )

        gateway._process_service(service)
        gateway._process_method(method)

        assert len(method.options) == 1
        expected_option = """(google.api.http) = {
    get: "/api/users/{user_id}"
  }"""
        assert method.options[0] == expected_option
        assert len(gateway.errors) == 0
        assert "google/api/annotations.proto" in service.module_level_imports

    def test_process_method_with_complex_gateway(self):
        """Test processing method with complex gateway configuration"""
        gateway = AddGateway()
        service = MockService()
        method = MockMethod(
            name="create_user",
            meta={
                "gateway": {
                    "post": "/api/users",
                    "body": "*",
                    "additional_bindings": [{"post": "/api/v1/users", "body": "*"}],
                }
            },
        )

        gateway._process_service(service)
        gateway._process_method(method)

        assert len(method.options) == 1
        expected_option = """(google.api.http) = {
    post: "/api/users"
    body: "*"
    additional_bindings: [ { post: "/api/v1/users" body: "*" } ]
  }"""
        assert method.options[0] == expected_option
        assert "google/api/annotations.proto" in service.module_level_imports

    def test_process_method_with_invalid_gateway_data(self):
        """Test processing method with invalid gateway data"""
        gateway = AddGateway()
        service = MockService()
        method = MockMethod(
            name="invalid_method",
            meta={
                "gateway": {"get": "/api/test", "invalid": object()}  # Unsupported type
            },
        )

        gateway._process_service(service)
        gateway._process_method(method)

        assert len(method.options) == 0  # No option added due to error
        assert "invalid_method" in gateway.errors
        assert len(gateway.errors["invalid_method"]) == 1
        assert "Unsupported type" in gateway.errors["invalid_method"][0]
        assert (
            "google/api/annotations.proto" in service.module_level_imports
        )  # Import still added

    def test_multiple_methods_with_gateway(self):
        """Test processing multiple methods with gateway metadata"""
        gateway = AddGateway()
        service = MockService()

        method1 = MockMethod(
            name="get_user", meta={"gateway": {"get": "/api/users/{id}"}}
        )
        method2 = MockMethod(
            name="create_user", meta={"gateway": {"post": "/api/users", "body": "*"}}
        )

        gateway._process_service(service)
        gateway._process_method(method1)
        gateway._process_method(method2)

        assert len(method1.options) == 1
        assert len(method2.options) == 1
        assert len(gateway.errors) == 0
        assert "google/api/annotations.proto" in service.module_level_imports

    def test_close_with_no_errors(self):
        """Test close method with no errors"""
        gateway = AddGateway()
        service = MockService()
        method = MockMethod(name="test_method", meta={"gateway": {"get": "/api/test"}})

        gateway._process_service(service)
        gateway._process_method(method)
        gateway.close()  # Should not raise

    def test_close_with_errors_raises_exception(self):
        """Test close method with errors raises ValueError"""
        gateway = AddGateway()
        service = MockService()
        method = MockMethod(
            name="error_method",
            meta={"gateway": {"get": "/api/test", "invalid": object()}},
        )

        gateway._process_service(service)
        gateway._process_method(method)

        with pytest.raises(ValueError, match="Gateway option errors"):
            gateway.close()

    def test_multiple_errors_collected(self):
        """Test that multiple errors are collected correctly"""
        gateway = AddGateway()
        service = MockService()

        method1 = MockMethod(
            name="error_method1",
            meta={"gateway": {"get": "/api/test", "invalid1": object()}},
        )
        method2 = MockMethod(
            name="error_method2",
            meta={"gateway": {"post": "/api/test", "invalid2": set()}},
        )

        gateway._process_service(service)
        gateway._process_method(method1)
        gateway._process_method(method2)

        assert len(gateway.errors) == 2
        assert "error_method1" in gateway.errors
        assert "error_method2" in gateway.errors

        with pytest.raises(ValueError, match="Gateway option errors"):
            gateway.close()

    def test_complex_nested_structure(self):
        """Test complex nested structures with multiple data types"""
        mapping = {
            "post": "/v1/users",
            "body": "*",
            "timeout": 30,
            "extra": {"header": "x-api-key", "secure": False, "retries": 3},
            "bindings": ["/v1/a", "/v1/b"],
            "metadata": {
                "auth": {"required": True, "methods": ["oauth", "jwt"]},
                "cache": 300,
            },
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    post: "/v1/users"
    body: "*"
    timeout: 30
    extra: { header: "x-api-key" secure: false retries: 3 }
    bindings: [ "/v1/a", "/v1/b" ]
    metadata: { auth: { required: true methods: [ "oauth", "jwt" ] } cache: 300 }
  }"""
        assert result == expected

    def test_deeply_nested_objects(self):
        """Test deeply nested object structures"""
        mapping = {
            "get": "/api/test",
            "config": {
                "security": {
                    "auth": {"oauth": {"scopes": ["read", "write"], "required": True}}
                }
            },
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/test"
    config: { security: { auth: { oauth: { scopes: [ "read", "write" ] required: true } } } }
  }"""
        assert result == expected

    def test_mixed_array_types(self):
        """Test arrays with mixed data types"""
        mapping = {
            "post": "/api/bulk",
            "body": "*",
            "priorities": [1, 2, 3],
            "features": ["fast", "secure"],
            "settings": [
                {"name": "timeout", "value": 30},
                {"name": "retries", "value": 3},
            ],
            "flags": [True, False, True],
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    post: "/api/bulk"
    body: "*"
    priorities: [ 1, 2, 3 ]
    features: [ "fast", "secure" ]
    settings: [ { name: "timeout" value: 30 }, { name: "retries" value: 3 } ]
    flags: [ true, false, true ]
  }"""
        assert result == expected

    def test_empty_structures(self):
        """Test empty objects and arrays"""
        mapping = {
            "get": "/api/test",
            "empty_object": {},
            "empty_array": [],
            "partial_empty": {"data": [], "config": {}},
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/test"
    empty_object: {  }
    empty_array: [  ]
    partial_empty: { data: [  ] config: {  } }
  }"""
        assert result == expected

    def test_special_characters_in_strings(self):
        """Test strings with special characters"""
        mapping = {
            "get": "/api/test/{id}",
            "pattern": "user_{id}_data",
            "description": "Get user's profile data",
            "regex": r"^[a-zA-Z0-9_-]+$",
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/test/{id}"
    pattern: "user_{id}_data"
    description: "Get user's profile data"
    regex: "^[a-zA-Z0-9_-]+$"
  }"""
        assert result == expected

    def test_very_complex_additional_bindings(self):
        """Test very complex additional bindings with nested structures"""
        mapping = {
            "get": "/v1/users/{user_id}",
            "additional_bindings": [
                {"get": "/v2/users/{user_id}", "response_body": "user", "timeout": 10},
                {
                    "post": "/v1/users/{user_id}/actions",
                    "body": "action",
                    "metadata": {"version": 1, "deprecated": False},
                },
            ],
            "custom_options": {
                "auth": ["jwt", "oauth"],
                "rate_limit": 100,
                "features": {"caching": True, "compression": False},
            },
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/v1/users/{user_id}"
    additional_bindings: [ { get: "/v2/users/{user_id}" response_body: "user" timeout: 10 }, { post: "/v1/users/{user_id}/actions" body: "action" metadata: { version: 1 deprecated: false } } ]
    custom_options: { auth: [ "jwt", "oauth" ] rate_limit: 100 features: { caching: true compression: false } }
  }"""
        assert result == expected

    def test_numeric_edge_cases(self):
        """Test various numeric types and edge cases"""
        mapping = {
            "get": "/api/test",
            "zero": 0,
            "negative": -42,
            "float_zero": 0.0,
            "large_number": 999999999,
            "scientific": 1e6,
            "decimal": 123.456789,
        }
        result = proto_http_option(mapping)

        expected = """(google.api.http) = {
    get: "/api/test"
    zero: 0
    negative: -42
    float_zero: 0.0
    large_number: 999999999
    scientific: 1000000.0
    decimal: 123.456789
  }"""
        assert result == expected

    def test_real_world_complex_gateway_setup(self):
        """Test real-world complex gateway setup"""
        gateway = AddGateway()
        service = MockService()
        method = MockMethod(
            name="complex_api_method",
            meta={
                "gateway": {
                    "post": "/v1/users",
                    "body": "*",
                    "timeout": 30,
                    "extra": {"header": "x-api-key", "secure": False},
                    "bindings": ["/v1/a", "/v1/b"],
                    "additional_bindings": [
                        {"get": "/v1/users/{id}", "timeout": 10},
                        {"put": "/v1/users/{id}", "body": "*", "response_body": "user"},
                    ],
                }
            },
        )

        gateway._process_service(service)
        gateway._process_method(method)

        assert len(method.options) == 1
        expected_option = """(google.api.http) = {
    post: "/v1/users"
    body: "*"
    timeout: 30
    extra: { header: "x-api-key" secure: false }
    bindings: [ "/v1/a", "/v1/b" ]
    additional_bindings: [ { get: "/v1/users/{id}" timeout: 10 }, { put: "/v1/users/{id}" body: "*" response_body: "user" } ]
  }"""
        assert method.options[0] == expected_option
        assert len(gateway.errors) == 0
        assert "google/api/annotations.proto" in service.module_level_imports

    def test_real_world_rest_api_patterns(self):
        """Test real-world REST API patterns"""
        gateway = AddGateway()
        service = MockService()

        # GET single resource
        get_method = MockMethod(
            name="get_user", meta={"gateway": {"get": "/v1/users/{user_id}"}}
        )

        # POST create resource
        post_method = MockMethod(
            name="create_user", meta={"gateway": {"post": "/v1/users", "body": "*"}}
        )

        # PUT update resource
        put_method = MockMethod(
            name="update_user",
            meta={"gateway": {"put": "/v1/users/{user_id}", "body": "*"}},
        )

        # PATCH partial update
        patch_method = MockMethod(
            name="patch_user",
            meta={"gateway": {"patch": "/v1/users/{user_id}", "body": "*"}},
        )

        # DELETE resource
        delete_method = MockMethod(
            name="delete_user", meta={"gateway": {"delete": "/v1/users/{user_id}"}}
        )

        # LIST with query parameters
        list_method = MockMethod(
            name="list_users", meta={"gateway": {"get": "/v1/users"}}
        )

        methods = [
            get_method,
            post_method,
            put_method,
            patch_method,
            delete_method,
            list_method,
        ]

        gateway._process_service(service)
        for method in methods:
            gateway._process_method(method)

        # All methods should have gateway options
        for method in methods:
            assert len(method.options) == 1
            assert "(google.api.http)" in method.options[0]

        assert len(gateway.errors) == 0
        assert "google/api/annotations.proto" in service.module_level_imports
