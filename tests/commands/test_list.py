import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from grpcAPI.app import APIService, App
from grpcAPI.commands.list import ListCommand
from grpcAPI.makeproto.interface import ILabeledMethod, IMetaType


@pytest.fixture
def mock_method() -> Mock:
    """Create a mock method with required attributes"""
    method = Mock(spec=ILabeledMethod)
    method.name = "test_method"
    method.active = True
    method.options = []
    method.description = ""  # Default empty description

    # Mock request types
    mock_req_type = Mock(spec=IMetaType)
    mock_argtype = Mock()
    mock_argtype.__name__ = "TestRequest"
    mock_req_type.argtype = mock_argtype
    method.request_types = [mock_req_type]

    # Mock response type
    mock_resp_type = Mock(spec=IMetaType)
    mock_resp_argtype = Mock()
    mock_resp_argtype.__name__ = "TestResponse"
    mock_resp_type.argtype = mock_resp_argtype
    method.response_types = mock_resp_type

    return method


@pytest.fixture
def mock_service(mock_method) -> APIService:
    """Create a mock service with a method"""
    service = APIService(
        name="TestService",
        package="test.package",
        module="test_module",
        description="A test service",
    )
    service._APIService__methods = [mock_method]
    # Services are assumed to be already filtered, so no need to set active
    return service


class TestListCommandConsoleOutput:
    """Test the ListCommand console output"""

    def test_display_empty_services(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test display with no services"""
        app = App()
        cmd = ListCommand(app, None)
        cmd.run_sync()
        captured = capsys.readouterr()
        assert "No services registered" in captured.out

    def test_display_services_with_description(self, mock_service, capsys):
        """Test display shows service description properly"""
        with patch("grpcAPI.commands.command.run_process_service"):
            mock_service.description = "Test service description"
            mock_service.comments = "Test comments"

            app = App()
            app.add_service(mock_service)
            cmd = ListCommand(app, None)

            cmd.run_sync(show_descriptions=True)
            captured = capsys.readouterr()

            assert "TestService" in captured.out
            assert "1 service(s)" in captured.out
            assert "1 method(s)" in captured.out

    def test_display_services_shows_all_services(self, mock_service, capsys):
        """Test display shows all services"""
        with patch("grpcAPI.commands.command.run_process_service"):
            app = App()
            app.add_service(mock_service)
            cmd = ListCommand(app, None)

            cmd.run_sync()
            captured = capsys.readouterr()

            assert "TestService" in captured.out
            assert "test.package" in captured.out
            assert "test_method" in captured.out

    def test_service_description_priority(self, mock_method, capsys):
        """Test that service description takes priority over comments"""
        with patch("grpcAPI.commands.command.run_process_service"):
            service = APIService(
                name="TestService",
                package="test.package",
                module="test_module",
                description="Service description",
            )
            service.comments = "Service comments"
            service._APIService__methods = [mock_method]

            app = App()
            app.add_service(service)
            cmd = ListCommand(app, None)

            cmd.run_sync(show_descriptions=True)
            captured = capsys.readouterr()

            # Should show service description, not comments
            assert "Service description" in captured.out
            assert "Service comments" not in captured.out

    def test_service_fallback_to_comments(self, mock_method, capsys):
        """Test that service falls back to comments when no description"""
        with patch("grpcAPI.commands.command.run_process_service"):
            service = APIService(
                name="TestService",
                package="test.package",
                module="test_module",
                description="",  # Empty description
            )
            service.comments = "Service comments"
            service._APIService__methods = [mock_method]

            app = App()
            app.add_service(service)
            cmd = ListCommand(app, None)

            cmd.run_sync(show_descriptions=True)
            captured = capsys.readouterr()

            # Should show service comments when no description
            assert "Service comments" in captured.out

    def test_service_no_description_or_comments(self, mock_method, capsys):
        """Test that service handles empty descriptions gracefully"""
        with patch("grpcAPI.commands.command.run_process_service"):
            service = APIService(
                name="TestService",
                package="test.package",
                module="test_module",
                description="",
            )
            service.comments = ""
            service._APIService__methods = [mock_method]

            app = App()
            app.add_service(service)
            cmd = ListCommand(app, None)

            cmd.run_sync(show_descriptions=True)
            captured = capsys.readouterr()

            # Should still show service name and structure without descriptions
            assert "TestService" in captured.out
            assert "test.package" in captured.out


class TestListCommand:
    """Test the ListCommand class"""

    def test_list_command_init(self, mock_service):
        """Test ListCommand initialization"""
        with patch("grpcAPI.commands.command.run_process_service") as mock_run_process:
            # Create app directly and pass to command
            app = App()
            app.add_service(mock_service)

            cmd = ListCommand(app, None)

            assert cmd.command_name == "list"
            assert cmd.app is app
            assert cmd._is_sync is True
            assert isinstance(cmd.app, App)

            # Verify run_process_service was called
            mock_run_process.assert_called_once_with(app, cmd.settings, [])

    def test_list_command_with_settings(self, mock_service):
        """Test ListCommand with settings file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": "value"}')
            settings_path = f.name

        try:
            with patch("grpcAPI.commands.command.run_process_service"), patch(
                "grpcAPI.commands.command.load_file_by_extension"
            ) as mock_load_file:

                mock_load_file.return_value = {"test": "value"}

                # Create app directly
                app = App()
                app.add_service(mock_service)

                cmd = ListCommand(app, settings_path)

                assert cmd.settings_path == settings_path
                mock_load_file.assert_called_once()
        finally:
            Path(settings_path).unlink()

    def test_list_command_run(self, mock_service, capsys):
        """Test ListCommand.run_sync() method"""
        with patch("grpcAPI.commands.command.run_process_service"):
            # Create app directly
            app = App()
            app.add_service(mock_service)

            cmd = ListCommand(app, None)

            result = cmd.execute()
            captured = capsys.readouterr()

            # Verify actual output content
            assert "TestService" in captured.out
            assert "1 service(s)" in captured.out
            assert "1 method(s)" in captured.out

            # Result should be None since we display directly
            assert result is None

    def test_multiple_commands_with_same_app(self, mock_service):
        """Test that multiple ListCommand instances can use the same app instance"""
        with patch("grpcAPI.commands.command.run_process_service"):
            # Create single app instance
            app = App()
            app.add_service(mock_service)

            # Create multiple commands with same app
            cmd1 = ListCommand(app, None)
            cmd2 = ListCommand(app, None)

            # Both should reference the same app instance
            assert cmd1.app is cmd2.app
            assert cmd1.app is app


class TestListOutputDemo:
    """Demo test to show list command output format"""

    def test_real_console_output(
        self, mock_service, capsys: pytest.CaptureFixture[str]
    ):
        """Test that actually shows console output"""

        # Create multiple mock services for demo
        service1 = APIService(
            name="UserService",
            package="account",
            module="user",
            description="Manages user accounts and authentication",
        )

        service2 = APIService(
            name="RideService",
            package="ride",
            module="booking",
            description="Handles ride booking and management",
        )

        # Create mock methods
        method1 = Mock(spec=ILabeledMethod)
        method1.name = "GetUser"
        method1.active = True
        method1.options = []
        method1.description = ""

        # Mock request/response types for method1
        req_type1 = Mock(spec=IMetaType)
        req_type1.argtype = Mock()
        req_type1.argtype.__name__ = "GetUserRequest"
        method1.request_types = [req_type1]

        resp_type1 = Mock(spec=IMetaType)
        resp_type1.argtype = Mock()
        resp_type1.argtype.__name__ = "UserResponse"
        method1.response_types = resp_type1

        method2 = Mock(spec=ILabeledMethod)
        method2.name = "BookRide"
        method2.active = True
        method2.options = []
        method2.description = ""

        # Mock request/response types for method2
        req_type2 = Mock(spec=IMetaType)
        req_type2.argtype = Mock()
        req_type2.argtype.__name__ = "BookRideRequest"
        method2.request_types = [req_type2]

        resp_type2 = Mock(spec=IMetaType)
        resp_type2.argtype = Mock()
        resp_type2.argtype.__name__ = "RideResponse"
        method2.response_types = resp_type2

        # Add methods to services
        service1._APIService__methods = [method1]
        service2._APIService__methods = [method2]

        services = [service1, service2]

        # Actually execute the console output via ListCommand
        with patch("grpcAPI.commands.command.run_process_service"):
            app = App()
            for service in services:
                app.add_service(service)

            cmd = ListCommand(app, None)

            print("\n" + "=" * 60)
            print("GRPC API LIST COMMAND OUTPUT EXAMPLE")
            print("=" * 60)
            cmd.run_sync(show_descriptions=True)
            print("=" * 60)

        # Capture and verify output was generated
        captured = capsys.readouterr()
        assert "GRPC API LIST COMMAND OUTPUT EXAMPLE" in captured.out
        assert "UserService" in captured.out
        assert "RideService" in captured.out


class TestListCommandWithFunctionalService:
    """Test ListCommand using functional_service fixture for more realistic testing"""

    def test_list_command_with_functional_service(self, functional_service):
        """Test ListCommand with functional service fixture"""
        with patch("grpcAPI.commands.command.run_process_service"):
            # Create app directly
            app = App()
            app.add_service(functional_service)

            cmd = ListCommand(app, None)

            # Verify functional service was added
            assert len(cmd.app.service_list) == 1
            service = cmd.app.service_list[0]
            assert service.name == "functional"
            assert service.module == "account_service"
            assert service.active is True

            # Verify it has real methods
            assert len(service.methods) > 0
            method_names = [method.name for method in service.methods]
            assert "create_account" in method_names
            assert "get_accounts" in method_names

    def test_functional_service_display_output(
        self, functional_service, capsys: pytest.CaptureFixture[str]
    ):
        """Test display output with functional service - shows real method signatures"""

        with patch("grpcAPI.commands.command.run_process_service"):
            app = App()
            app.add_service(functional_service)
            cmd = ListCommand(app, None)

            print("\n" + "=" * 70)
            print("FUNCTIONAL SERVICE LIST OUTPUT")
            print("=" * 70)
            cmd.run_sync(show_descriptions=True)
            print("=" * 70)

        # Capture and verify output was generated
        captured = capsys.readouterr()
        assert "FUNCTIONAL SERVICE LIST OUTPUT" in captured.out
        assert "functional" in captured.out
        assert "create_account" in captured.out

        # Verify the service can be displayed without errors
        with patch("grpcAPI.commands.command.run_process_service"):
            app = App()
            app.add_service(functional_service)
            cmd = ListCommand(app, None)

            cmd.run_sync()
            captured = capsys.readouterr()

            # Verify actual output content
            assert "functional" in captured.out
            assert "create_account" in captured.out
            assert "1 service(s)" in captured.out

    def test_multiple_services_mixed_types(
        self, functional_service, mock_service, capsys
    ):
        """Test display with both functional and mock services"""

        services = [functional_service, mock_service]

        with patch("grpcAPI.commands.command.run_process_service"):
            app = App()
            for service in services:
                app.add_service(service)
            cmd = ListCommand(app, None)

            cmd.run_sync()
            captured = capsys.readouterr()

            # Should handle both service types
            assert "functional" in captured.out
            assert "TestService" in captured.out
            assert "2 service(s)" in captured.out
