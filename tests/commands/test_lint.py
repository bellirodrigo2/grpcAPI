import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from grpcAPI.app import APIService, App, GrpcAPI
from grpcAPI.commands.lint import LintCommand, run_lint
from grpcAPI.makeproto.interface import IProtoPackage


@pytest.fixture
def mock_app_module() -> Mock:
    """Mock app module that creates a GrpcAPI instance with services"""
    mock_module = Mock()

    def mock_load_app(app_path: str):
        # Simulate app module creating and populating the singleton
        app = GrpcAPI()
        # Use the functional_service fixture data to populate the singleton
        from conftest import functional_service

        service = functional_service()
        app.add_service(service)

    mock_module.load_app = mock_load_app
    return mock_module


class TestRunLint:
    """Test the run_lint function directly"""

    def test_run_lint_with_services(self, functional_service: APIService) -> None:
        """Test run_lint generates proto files from services"""
        app = App()  # App is NOT singleton
        app.add_service(functional_service)

        logger = Mock()

        # Mock the make_protos function to return sample proto packages
        mock_proto = Mock(spec=IProtoPackage)
        mock_proto.package = "test_package"
        mock_proto.filename = "test_service"
        mock_proto.content = 'syntax = "proto3";\nservice TestService {}'

        with patch("grpcAPI.commands.lint.make_protos") as mock_make_protos:
            mock_make_protos.return_value = [mock_proto]

            result = run_lint(app, logger)

            # Verify make_protos was called with app.services
            mock_make_protos.assert_called_once_with(app.services)

            # Verify logger was called
            logger.info.assert_called_with("1 Protos have been successfully generated.")
            logger.debug.assert_called_with(
                "Generated files:", [("test_package", "test_service")]
            )

            # Verify result
            result_list = list(result)
            assert len(result_list) == 1
            assert result_list[0] is mock_proto

    def test_run_lint_empty_services(self):
        """Test run_lint with empty services"""
        app = App()  # No services added
        logger = Mock()

        with patch("grpcAPI.commands.lint.make_protos") as mock_make_protos:
            mock_make_protos.return_value = []

            result = run_lint(app, logger)

            # Verify make_protos was called
            mock_make_protos.assert_called_once_with(app.services)

            # Verify logger was still called
            logger.info.assert_called_with("0 Protos have been successfully generated.")
            logger.debug.assert_called_with("Generated files:", [])

            # Verify empty result
            result_list = list(result)
            assert len(result_list) == 0


class TestLintCommand:
    """Test the LintCommand class"""

    def test_lint_command_init(self, functional_service: APIService):
        """Test LintCommand initialization"""
        with patch("grpcAPI.commands.command.run_process_service") as mock_run_process:
            # Create app directly and pass to command
            app = App()
            app.add_service(functional_service)

            cmd = LintCommand(app, None)

            assert cmd.command_name == "lint"
            assert cmd.app is app
            assert cmd.settings_path is None
            assert isinstance(cmd.app, App)

            # Verify run_process_service was called
            mock_run_process.assert_called_once_with(app, cmd.settings, [])

    def test_lint_command_with_settings(self, app_fixture: App):
        """Test LintCommand with settings file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": "value"}')
            settings_path = f.name

        try:
            with patch("grpcAPI.commands.command.run_process_service"), patch(
                "grpcAPI.commands.command.load_file_by_extension"
            ) as mock_load_file:

                # Mock file loading
                mock_load_file.return_value = {"test": "value"}

                # Use app_fixture directly
                app = app_fixture

                cmd = LintCommand(app, settings_path)

                assert cmd.settings_path == settings_path
                mock_load_file.assert_called_once()
        finally:
            Path(settings_path).unlink()

    def test_lint_command_run(self, app_fixture: App) -> None:
        """Test LintCommand.run() method"""
        with patch("grpcAPI.commands.command.run_process_service"):
            # Use app_fixture directly
            app = app_fixture

            cmd = LintCommand(app, None)

            with patch("grpcAPI.commands.lint.run_lint") as mock_run_lint:
                mock_proto = Mock(spec=IProtoPackage)
                mock_run_lint.return_value = [mock_proto]

                cmd.execute()

                # Verify run_lint was called with the app instance
                mock_run_lint.assert_called_once_with(cmd.app, cmd.logger)

    def test_multiple_commands_with_same_app(self, app_fixture: App) -> None:
        """Test that multiple LintCommand instances can use the same app instance"""
        with patch("grpcAPI.commands.command.run_process_service"):
            # Use app_fixture directly
            app = app_fixture

            # Create multiple commands with same app
            cmd1 = LintCommand(app, None)
            cmd2 = LintCommand(app, None)

            # Both should reference the same app instance
            assert cmd1.app is cmd2.app
            assert cmd1.app is app

    def test_app_vs_grpcapi_difference(self, app_fixture: App) -> None:
        """Test that App() creates new instances while commands can use either"""
        with patch("grpcAPI.commands.command.run_process_service"):
            # Create regular App instances (not singleton)
            app1 = App()
            app2 = App()

            # Regular App instances are different
            assert app1 is not app2

            # Create LintCommand instances with different apps
            cmd1 = LintCommand(app1, None)
            cmd2 = LintCommand(app2, None)

            # Commands use different app instances
            assert cmd1.app is not cmd2.app
            assert cmd1.app is app1
            assert cmd2.app is app2

            # Test with app_fixture
            cmd3 = LintCommand(app_fixture, None)
            assert cmd3.app is app_fixture
