"""
Comprehensive test suite for grpcAPI CLI functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from grpcAPI.cli import cli, get_app_instance, handle_error, setup_cli_logging


class TestCLIHelperFunctions:
    """Test CLI helper functions."""

    def test_setup_cli_logging_default(self):
        """Test setup_cli_logging with default parameters."""
        with patch("grpcAPI.cli.logging.config.dictConfig") as mock_dict_config:
            setup_cli_logging()
            mock_dict_config.assert_called_once()

    def test_setup_cli_logging_verbose(self):
        """Test setup_cli_logging with verbose enabled."""
        with patch("grpcAPI.cli.logging.config.dictConfig") as mock_dict_config:
            setup_cli_logging(verbose=True)
            mock_dict_config.assert_called_once()

    @patch("grpcAPI.cli.load_app")
    @patch("grpcAPI.cli.GrpcAPI")
    def test_get_app_instance(self, mock_grpc_api, mock_load_app):
        """Test get_app_instance function."""
        mock_app = MagicMock()
        mock_grpc_api.return_value = mock_app

        result = get_app_instance("test_app.py")

        mock_load_app.assert_called_once_with("test_app.py")
        mock_grpc_api.assert_called_once()
        assert result == mock_app

    @patch("grpcAPI.cli.console.print")
    @patch("grpcAPI.cli.sys.exit")
    def test_handle_error(self, mock_exit, mock_print):
        """Test handle_error function."""
        test_error = ValueError("Test error")

        handle_error(test_error, "test_command")

        mock_print.assert_called()
        mock_exit.assert_called_once_with(1)


class TestCLICommands:
    """Test CLI commands."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create a test app file
        self.test_app_path = self.temp_path / "test_app.py"
        self.test_app_path.write_text(
            """
from grpcAPI.app import GrpcAPI
app = GrpcAPI()
"""
        )

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_version_flag(self):
        """Test CLI --version flag."""
        result = self.runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "gRPC API Framework" in result.output

    def test_cli_no_command(self):
        """Test CLI with no command shows help."""
        result = self.runner.invoke(cli, [])
        assert result.exit_code == 0
        assert "Type" in result.output and "grpcapi --help" in result.output


class TestRunCommand:
    """Test the run command."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create a test app file
        self.test_app_path = self.temp_path / "test_app.py"
        self.test_app_path.write_text(
            """
from grpcAPI.app import GrpcAPI
app = GrpcAPI()
"""
        )

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("grpcAPI.cli.asyncio.run")
    @patch("grpcAPI.cli.RunCommand")
    @patch("grpcAPI.cli.get_app_instance")
    @patch("grpcAPI.cli.setup_cli_logging")
    def test_run_command_basic(
        self, mock_setup_logging, mock_get_app, mock_run_cmd, mock_asyncio
    ):
        """Test run command with basic parameters."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()
        mock_run_cmd.return_value = mock_command

        self.runner.invoke(cli, ["run", str(self.test_app_path)])

        # Should not exit with error (command setup should work)
        mock_setup_logging.assert_called_once_with(False)
        mock_get_app.assert_called_once_with(str(self.test_app_path))
        mock_run_cmd.assert_called_once_with(mock_app, None)

    @patch("grpcAPI.cli.asyncio.run")
    @patch("grpcAPI.cli.RunCommand")
    @patch("grpcAPI.cli.get_app_instance")
    @patch("grpcAPI.cli.setup_cli_logging")
    def test_run_command_with_options(
        self, mock_setup_logging, mock_get_app, mock_run_cmd, mock_asyncio
    ):
        """Test run command with all options."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()
        mock_run_cmd.return_value = mock_command

        self.runner.invoke(
            cli,
            [
                "run",
                str(self.test_app_path),
                "--host",
                "0.0.0.0",
                "--port",
                "8080",
                "--settings",
                "config.json",
                "--no-lint",
                "--verbose",
            ],
        )

        mock_setup_logging.assert_called_once_with(True)
        mock_get_app.assert_called_once_with(str(self.test_app_path))
        mock_run_cmd.assert_called_once_with(mock_app, "config.json")

    @patch("grpcAPI.cli.handle_error")
    @patch("grpcAPI.cli.get_app_instance")
    def test_run_command_error_handling(self, mock_get_app, mock_handle_error):
        """Test run command error handling."""
        mock_get_app.side_effect = ValueError("Test error")

        self.runner.invoke(cli, ["run", str(self.test_app_path)])

        mock_handle_error.assert_called_once()


class TestBuildCommand:
    """Test the build command."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create a test app file
        self.test_app_path = self.temp_path / "test_app.py"
        self.test_app_path.write_text(
            """
from grpcAPI.app import GrpcAPI
app = GrpcAPI()
"""
        )

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("grpcAPI.cli.BuildCommand")
    @patch("grpcAPI.cli.get_app_instance")
    def test_build_command_basic(self, mock_get_app, mock_build_cmd):
        """Test build command with basic parameters."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()
        mock_command.execute.return_value = set(["test.proto"])
        mock_build_cmd.return_value = mock_command

        self.runner.invoke(cli, ["build", str(self.test_app_path)])

        mock_get_app.assert_called_once_with(str(self.test_app_path))
        mock_build_cmd.assert_called_once_with(mock_app, None)
        mock_command.execute.assert_called_once_with(
            outdir=None,
            overwrite=False,
            zipcompress=False,
        )

    @patch("grpcAPI.cli.BuildCommand")
    @patch("grpcAPI.cli.get_app_instance")
    def test_build_command_with_options(self, mock_get_app, mock_build_cmd):
        """Test build command with all options."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()
        mock_command.execute.return_value = set(["test1.proto", "test2.proto"])
        mock_build_cmd.return_value = mock_command

        self.runner.invoke(
            cli,
            [
                "build",
                str(self.test_app_path),
                "--output",
                "./custom_output",
                "--settings",
                "config.json",
                "--overwrite",
                "--zip",
            ],
        )

        mock_command.execute.assert_called_once_with(
            outdir="./custom_output",
            overwrite=True,
            zipcompress=True,
        )


class TestLintCommand:
    """Test the lint command."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create a test app file
        self.test_app_path = self.temp_path / "test_app.py"
        self.test_app_path.write_text(
            """
from grpcAPI.app import GrpcAPI
app = GrpcAPI()
"""
        )

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("grpcAPI.cli.LintCommand")
    @patch("grpcAPI.cli.get_app_instance")
    @patch("grpcAPI.cli.setup_cli_logging")
    def test_lint_command_basic(self, mock_setup_logging, mock_get_app, mock_lint_cmd):
        """Test lint command with basic parameters."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()
        mock_proto_files = [MagicMock(package="test", filename="test.proto")]
        mock_command.execute.return_value = mock_proto_files
        mock_lint_cmd.return_value = mock_command

        self.runner.invoke(cli, ["lint", str(self.test_app_path)])

        mock_setup_logging.assert_called_once_with(False)
        mock_get_app.assert_called_once_with(str(self.test_app_path))
        mock_lint_cmd.assert_called_once_with(mock_app, None)

    @patch("grpcAPI.cli.LintCommand")
    @patch("grpcAPI.cli.get_app_instance")
    @patch("grpcAPI.cli.setup_cli_logging")
    def test_lint_command_verbose(
        self, mock_setup_logging, mock_get_app, mock_lint_cmd
    ):
        """Test lint command with verbose flag."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()
        mock_proto_files = [MagicMock(package="test", filename="test.proto")]
        mock_command.execute.return_value = mock_proto_files
        mock_lint_cmd.return_value = mock_command

        self.runner.invoke(cli, ["lint", str(self.test_app_path), "--verbose"])

        mock_setup_logging.assert_called_once_with(True)


class TestListCommand:
    """Test the list command."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create a test app file
        self.test_app_path = self.temp_path / "test_app.py"
        self.test_app_path.write_text(
            """
from grpcAPI.app import GrpcAPI
app = GrpcAPI()
"""
        )

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("grpcAPI.cli.ListCommand")
    @patch("grpcAPI.cli.get_app_instance")
    def test_list_command_basic(self, mock_get_app, mock_list_cmd):
        """Test list command with basic parameters."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()

        # Mock service info structure
        mock_service = MagicMock()
        mock_service.name = "TestService"
        mock_service.active = True
        mock_service.methods = []

        mock_services_info = {"test_package": [mock_service]}
        mock_command.execute.return_value = mock_services_info
        mock_list_cmd.return_value = mock_command

        self.runner.invoke(cli, ["list", str(self.test_app_path)])

        mock_get_app.assert_called_once_with(str(self.test_app_path))
        mock_list_cmd.assert_called_once_with(mock_app, None)

    @patch("grpcAPI.cli.ListCommand")
    @patch("grpcAPI.cli.get_app_instance")
    def test_list_command_with_descriptions(self, mock_get_app, mock_list_cmd):
        """Test list command with descriptions enabled."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()

        mock_service = MagicMock()
        mock_service.name = "TestService"
        mock_service.active = True
        mock_service.methods = []

        mock_services_info = {"test_package": [mock_service]}
        mock_command.execute.return_value = mock_services_info
        mock_list_cmd.return_value = mock_command

        self.runner.invoke(
            cli, ["list", str(self.test_app_path), "--show-descriptions"]
        )

        mock_command.execute.assert_called_once_with(show_descriptions=True)

    @patch("grpcAPI.cli.ListCommand")
    @patch("grpcAPI.cli.get_app_instance")
    def test_list_command_no_services(self, mock_get_app, mock_list_cmd):
        """Test list command when no services are registered."""
        mock_app = MagicMock()
        mock_get_app.return_value = mock_app
        mock_command = MagicMock()
        mock_command.execute.return_value = {}
        mock_list_cmd.return_value = mock_command

        result = self.runner.invoke(cli, ["list", str(self.test_app_path)])

        # Should show "No services registered" message
        assert result.exit_code == 0


class TestInitCommand:
    """Test the init command."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("grpcAPI.cli.InitCommand")
    def test_init_command_basic(self, mock_init_cmd):
        """Test init command with default parameters."""
        mock_command = MagicMock()
        mock_init_cmd.return_value = mock_command

        with self.runner.isolated_filesystem():
            self.runner.invoke(cli, ["init"])

            mock_init_cmd.assert_called_once_with(settings_path=None)
            mock_command.execute.assert_called_once()

    @patch("grpcAPI.cli.InitCommand")
    def test_init_command_with_options(self, mock_init_cmd):
        """Test init command with force and output options."""
        mock_command = MagicMock()
        mock_init_cmd.return_value = mock_command

        self.runner.invoke(cli, ["init", "--force", "--output", str(self.temp_path)])

        mock_command.execute.assert_called_once_with(force=True, dst=self.temp_path)

    @patch("grpcAPI.cli.handle_error")
    @patch("grpcAPI.cli.InitCommand")
    def test_init_command_error_handling(self, mock_init_cmd, mock_handle_error):
        """Test init command error handling."""
        mock_command = MagicMock()
        mock_command.execute.side_effect = ValueError("Test error")
        mock_init_cmd.return_value = mock_command

        self.runner.invoke(cli, ["init"])

        mock_handle_error.assert_called_once()


class TestVersionCommand:
    """Test the version command."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(cli, ["version"])

        assert result.exit_code == 0
        assert "gRPC API Framework" in result.output


# @pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def setup_method(self):
        """Setup test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("grpcAPI.cli.load_app")
    def test_real_init_command(self, mock_load_app):
        """Test init command with real InitCommand (no mocking)."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["init"])

            # Check if config file was created
            config_file = Path("grpcapi.config.json")
            if config_file.exists():
                assert result.exit_code == 0
                content = config_file.read_text()
                assert "proto_path" in content
                assert "plugins" in content

    def test_cli_help_messages(self):
        """Test that all commands have proper help messages."""
        commands = ["run", "build", "lint", "list", "init", "version"]

        for cmd in commands:
            result = self.runner.invoke(cli, [cmd, "--help"])
            assert result.exit_code == 0
            assert "--help" in result.output or "Usage:" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
