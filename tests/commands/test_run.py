import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from grpcAPI.app import App
from grpcAPI.commands.run import RunCommand


class TestRunCommand:
    """Test the RunCommand class"""

    def test_run_command_init(self, app_fixture: App):
        """Test RunCommand initialization"""
        with patch("grpcAPI.commands.command.run_process_service") as mock_run_process:
            # Use app_fixture directly
            cmd = RunCommand(app_fixture, None)

            assert cmd.command_name == "run"
            assert cmd.app is app_fixture
            assert isinstance(cmd.app, App)

            # Verify run_process_service was called
            mock_run_process.assert_called_once_with(app_fixture, cmd.settings)

    def test_run_command_with_settings(self, app_fixture: App):
        """Test RunCommand with settings file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"host": "0.0.0.0", "port": 8080}')
            settings_path = f.name

        try:
            with patch("grpcAPI.commands.command.run_process_service"), patch(
                "grpcAPI.commands.command.load_file_by_extension"
            ) as mock_load_file:

                mock_load_file.return_value = {"host": "0.0.0.0", "port": 8080}

                cmd = RunCommand(app_fixture, settings_path)

                assert cmd.settings_path == settings_path
                mock_load_file.assert_called_once()
        finally:
            Path(settings_path).unlink()

    @pytest.mark.asyncio
    async def test_run_command_execution_flow(self, app_fixture: App):
        """Test RunCommand.run() method without actually starting server"""
        with patch("grpcAPI.commands.command.run_process_service"):
            cmd = RunCommand(app_fixture, None)

            # Mock all the server-related operations
            with patch("grpcAPI.commands.run.make_protos") as mock_make_protos, patch(
                "grpcAPI.commands.run.make_server"
            ) as mock_make_server, patch(
                "grpcAPI.commands.run.make_plugin"
            ) as mock_make_plugin, patch(
                "grpcAPI.commands.run.add_to_server"
            ) as mock_add_to_server:

                # Setup mocks
                mock_server = Mock()
                mock_server.add_insecure_port = Mock(return_value=50051)
                mock_server.register_plugin = Mock()
                mock_server.start = AsyncMock()
                mock_server.wait_for_termination = AsyncMock()

                mock_make_server.return_value = mock_server
                mock_make_protos.return_value = []
                mock_make_plugin.return_value = []

                # Mock AsyncExitStack to avoid actual lifespan management
                with patch("grpcAPI.commands.run.AsyncExitStack") as mock_stack:
                    mock_stack_instance = AsyncMock()
                    mock_stack.return_value.__aenter__ = AsyncMock(
                        return_value=mock_stack_instance
                    )
                    mock_stack.return_value.__aexit__ = AsyncMock(return_value=None)
                    mock_stack_instance.enter_async_context = AsyncMock()

                    # Execute the run command
                    await cmd.run(host="localhost", port=50051)

                    # Verify the execution flow
                    mock_make_protos.assert_called_once_with(cmd.app.services)
                    mock_make_server.assert_called_once()
                    mock_server.add_insecure_port.assert_called_once_with(
                        "localhost:50051"
                    )
                    mock_add_to_server.assert_called_once()
                    mock_server.start.assert_called_once()
                    mock_server.wait_for_termination.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_command_with_plugins(self, app_fixture: App):
        """Test RunCommand with plugins enabled"""
        with patch("grpcAPI.commands.command.run_process_service"), patch(
            "grpcAPI.commands.command.load_file_by_extension"
        ) as mock_load_file:

            mock_load_file.return_value = {
                "plugins": {
                    "additional": {},
                }
            }

            cmd = RunCommand(app_fixture, "settings.json")

            with patch("grpcAPI.commands.run.make_protos") as mock_make_protos, patch(
                "grpcAPI.commands.run.make_server"
            ) as mock_make_server, patch(
                "grpcAPI.commands.run.make_plugin"
            ) as mock_make_plugin:

                # Setup mocks
                mock_server = Mock()
                mock_server.add_insecure_port = Mock(return_value=50051)
                mock_server.register_plugin = Mock()
                mock_server.start = AsyncMock()
                mock_server.wait_for_termination = AsyncMock()

                mock_plugin = Mock()
                mock_make_server.return_value = mock_server
                mock_make_protos.return_value = []
                mock_make_plugin.return_value = mock_plugin

                with patch("grpcAPI.commands.run.AsyncExitStack") as mock_stack:
                    mock_stack_instance = AsyncMock()
                    mock_stack.return_value.__aenter__ = AsyncMock(
                        return_value=mock_stack_instance
                    )
                    mock_stack.return_value.__aexit__ = AsyncMock(return_value=None)
                    mock_stack_instance.enter_async_context = AsyncMock()

                    await cmd.run(host="localhost", port=50051)

                    # Verify plugins were created and registered
                    assert mock_make_plugin.call_count == 1  # health and reflection
                    mock_server.register_plugin.assert_called()

    @pytest.mark.asyncio
    async def test_run_command_with_custom_server(self, app_fixture: App):
        """Test RunCommand when app already has a server"""
        with patch("grpcAPI.commands.command.run_process_service"):
            # Set a custom server on the app_fixture
            app_fixture.server = Mock()

            cmd = RunCommand(app_fixture, None)

            with patch("grpcAPI.commands.run.make_protos") as mock_make_protos, patch(
                "grpcAPI.commands.run.ServerWrapper"
            ) as mock_server_wrapper, patch(
                "grpcAPI.commands.run.make_server"
            ) as mock_make_server:

                mock_server = Mock()
                mock_server.add_insecure_port = Mock(return_value=50051)
                mock_server.register_plugin = Mock()
                mock_server.start = AsyncMock()
                mock_server.wait_for_termination = AsyncMock()

                mock_server_wrapper.return_value = mock_server
                mock_make_protos.return_value = []

                with patch("grpcAPI.commands.run.AsyncExitStack") as mock_stack:
                    mock_stack_instance = AsyncMock()
                    mock_stack.return_value.__aenter__ = AsyncMock(
                        return_value=mock_stack_instance
                    )
                    mock_stack.return_value.__aexit__ = AsyncMock(return_value=None)
                    mock_stack_instance.enter_async_context = AsyncMock()

                    await cmd.run(host="localhost", port=50051)

                    # Verify custom server path was taken
                    mock_server_wrapper.assert_called_once_with(cmd.app.server)
                    mock_make_server.assert_not_called()

    def test_multiple_commands_with_same_app(self, app_fixture: App):
        """Test that multiple RunCommand instances can use the same app instance"""
        with patch("grpcAPI.commands.command.run_process_service"):
            # Create multiple commands with same app
            cmd1 = RunCommand(app_fixture, None)
            cmd2 = RunCommand(app_fixture, None)

            # Both should reference the same app instance
            assert cmd1.app is cmd2.app
            assert cmd1.app is app_fixture
