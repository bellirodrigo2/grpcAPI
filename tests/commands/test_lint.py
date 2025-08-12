import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from grpcAPI.app import APIService, App, GrpcAPI
from grpcAPI.commands.lint import LintCommand, run_lint
from grpcAPI.makeproto.interface import IProtoPackage
from grpcAPI.singleton import SingletonMeta


@pytest.fixture(autouse=True)
def reset_singleton():
    """Clear GrpcAPI singleton state before each test"""
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()


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
            logger.info.assert_called_with("Protos have been successfully generated.")
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
            logger.info.assert_called_with("Protos have been successfully generated.")
            logger.debug.assert_called_with("Generated files:", [])

            # Verify empty result
            result_list = list(result)
            assert len(result_list) == 0


class TestLintCommand:
    """Test the LintCommand class"""

    def test_lint_command_init(self):
        """Test LintCommand initialization"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ) as mock_run_process:

            # Mock load_app to setup singleton
            def setup_singleton(app_path: str):
                GrpcAPI()
                # Add empty services to avoid errors

            mock_load_app.side_effect = setup_singleton

            cmd = LintCommand("test_app:app", None)

            assert cmd.command_name == "lint"
            assert cmd.app_path == "test_app:app"
            assert cmd.settings_path is None
            assert isinstance(cmd.app, GrpcAPI)

            # Verify load_app was called
            mock_load_app.assert_called_once_with("test_app:app")
            mock_run_process.assert_called_once()

    def test_lint_command_with_settings(self):
        """Test LintCommand with settings file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": "value"}')
            settings_path = f.name

        try:
            with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
                "grpcAPI.commands.command.run_process_service"
            ), patch(
                "grpcAPI.commands.command.load_file_by_extension"
            ) as mock_load_file:

                # Mock file loading
                mock_load_file.return_value = {"test": "value"}

                def setup_singleton(app_path: str):
                    GrpcAPI()

                mock_load_app.side_effect = setup_singleton

                cmd = LintCommand("test_app:app", settings_path)

                assert cmd.settings_path == settings_path
                mock_load_file.assert_called_once()
        finally:
            Path(settings_path).unlink()

    def test_lint_command_run(self, functional_service: APIService) -> None:
        """Test LintCommand.run() method"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ):

            def setup_singleton(app_path: str):
                app = GrpcAPI()
                app.add_service(functional_service)

            mock_load_app.side_effect = setup_singleton

            cmd = LintCommand("test_app:app", None)

            with patch("grpcAPI.commands.lint.run_lint") as mock_run_lint:
                mock_proto = Mock(spec=IProtoPackage)
                mock_run_lint.return_value = [mock_proto]

                cmd.execute()

                # Verify run_lint was called with the singleton app instance
                mock_run_lint.assert_called_once_with(cmd.app, cmd.logger)

    def test_singleton_behavior_across_commands(
        self, functional_service: APIService
    ) -> None:
        """Test that multiple LintCommand instances share the same GrpcAPI singleton"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ):

            call_count = 0

            def setup_singleton(app_path: str):
                nonlocal call_count
                app = GrpcAPI()
                if call_count == 0:  # Only add service once
                    app.add_service(functional_service)
                call_count += 1

            mock_load_app.side_effect = setup_singleton

            # Create first command
            cmd1 = LintCommand("test_app:app", None)
            first_app_id = id(cmd1.app)

            # Create second command
            cmd2 = LintCommand("another_app:app", None)
            second_app_id = id(cmd2.app)

            # Both should reference the same singleton instance
            assert cmd1.app is cmd2.app
            assert first_app_id == second_app_id

    def test_app_vs_grpcapi_difference(self, functional_service: APIService) -> None:
        """Test that App() creates new instances but GrpcAPI() is singleton"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ):

            call_count = 0

            def setup_singleton(app_path: str):
                nonlocal call_count
                app = GrpcAPI()
                if call_count == 0:
                    app.add_service(functional_service)
                call_count += 1

            mock_load_app.side_effect = setup_singleton

            # Create regular App instances (not singleton)
            app1 = App()
            app2 = App()

            # Regular App instances are different
            assert app1 is not app2

            # Create LintCommand instances (uses GrpcAPI singleton)
            cmd1 = LintCommand("test_app:app", None)
            cmd2 = LintCommand("another_app:app", None)

            # GrpcAPI instances are the same (singleton)
            assert cmd1.app is cmd2.app

            # But different from regular App instances
            assert cmd1.app is not app1
            assert cmd1.app is not app2
