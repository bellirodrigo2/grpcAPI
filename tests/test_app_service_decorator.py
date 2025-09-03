import pytest

from grpcAPI import APIService, GrpcAPI
from grpcAPI.app import App
from grpcAPI.protobuf import StringValue


class TestAppServiceDecorator:

    def test_service_decorator_with_new_service(self):
        """Test that service decorator creates new service when not exists"""
        app = App()

        @app.service("test_service")
        def test_method(name: str) -> StringValue:
            return StringValue(value=f"Hello {name}")

        # Check service was created and added
        services = app.services
        assert "" in services  # default package
        assert len(services[""]) == 1

        service = services[""][0]
        assert service.name == "test_service"
        assert len(service.methods) == 1
        assert service.methods[0].name == "test_method"

    def test_service_decorator_with_existing_service(self):
        """Test that service decorator uses existing service when it exists"""
        app = App()

        # Pre-create service
        existing_service = APIService(name="existing_service")
        app.add_service(existing_service)

        @app.service("existing_service")
        def first_method(value: str) -> StringValue:
            return StringValue(value=value)

        @app.service("existing_service")
        def second_method(count: int) -> StringValue:
            return StringValue(value=str(count))

        # Check that methods were added to existing service
        services = app.services
        assert len(services[""]) == 1  # Still only one service

        service = services[""][0]
        assert service.name == "existing_service"
        assert len(service.methods) == 2

        method_names = [m.name for m in service.methods]
        assert "first_method" in method_names
        assert "second_method" in method_names

    def test_service_decorator_method_registration(self):
        """Test that decorated methods are properly registered"""
        app = App()

        @app.service("user_service")
        def get_user(user_id: str) -> StringValue:
            """Get user by ID"""
            return StringValue(value=f"User {user_id}")

        services = app.services
        service = services[""][0]
        method = service.methods[0]

        # Check method properties
        assert method.name == "get_user"
        assert method.method == get_user
        assert method.service == "user_service"
        assert method.package == ""
        assert method.module == "service"
        assert "Get user by ID" in method.comments

    def test_service_decorator_returns_original_function(self):
        """Test that decorator returns the original function unchanged"""
        app = App()

        @app.service("math_service")
        def add_numbers(a: int, b: int) -> int:
            return a + b

        # Function should work normally
        result = add_numbers(5, 3)
        assert result == 8

    def test_multiple_services_creation(self):
        """Test creating multiple different services"""
        app = App()

        @app.service("service_a")
        def method_a() -> StringValue:
            return StringValue(value="A")

        @app.service("service_b")
        def method_b() -> StringValue:
            return StringValue(value="B")

        services = app.services
        assert len(services[""]) == 2

        service_names = [s.name for s in services[""]]
        assert "service_a" in service_names
        assert "service_b" in service_names

    def test_service_decorator_with_grpcapi_singleton(self):
        """Test that decorator works with GrpcAPI singleton"""
        # Reset singleton for clean test
        if hasattr(GrpcAPI, "_instances"):
            GrpcAPI._instances.clear()

        app = GrpcAPI()

        @app.service("singleton_service")
        def singleton_method() -> StringValue:
            return StringValue(value="singleton")

        services = app.services
        assert len(services[""]) == 1
        assert services[""][0].name == "singleton_service"

    def test_service_lookup_in_services_dict(self):
        """Test that service lookup uses _services correctly"""
        app = App()

        # Create service directly in _services
        service = APIService(name="direct_service")
        app._services[""].append(service)

        @app.service("direct_service")
        def test_method() -> StringValue:
            return StringValue(value="test")

        # Should find existing service in _services
        services = app.services
        assert len(services[""]) == 1
        assert len(services[""][0].methods) == 1
        assert services[""][0].methods[0].name == "test_method"

    def test_service_decorator_error_handling(self):
        """Test that service decorator handles function registration properly"""
        app = App()

        @app.service("error_service")
        def valid_method() -> StringValue:
            return StringValue(value="valid")

        # Verify the method was registered without errors
        services = app.services
        service = services[""][0]
        assert len(service.methods) == 1
        assert service.methods[0].name == "valid_method"
