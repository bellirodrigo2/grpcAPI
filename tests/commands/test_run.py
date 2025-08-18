import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from grpcAPI.app import APIService, GrpcAPI
from grpcAPI.commands.run import RunCommand
from grpcAPI.singleton import SingletonMeta


@pytest.fixture(autouse=True)
def reset_singleton():
    """Clear GrpcAPI singleton state before each test"""
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()


@pytest.fixture(autouse=True)
def isolate_logging_config():
    """Isolate LOGGING_CONFIG to prevent test interference"""
    from grpcAPI.logger import LOGGING_CONFIG
    import logging.config
    
    # Deep copy to preserve nested dicts
    import copy
    original_config = copy.deepcopy(LOGGING_CONFIG)
    
    # Also backup actual logger state
    original_loggers = {}
    for name in logging.Logger.manager.loggerDict:
        if isinstance(logging.Logger.manager.loggerDict[name], logging.Logger):
            logger = logging.Logger.manager.loggerDict[name]
            original_loggers[name] = {
                'level': logger.level,
                'handlers': logger.handlers.copy(),
                'propagate': logger.propagate
            }
    
    yield
    
    # Restore LOGGING_CONFIG
    LOGGING_CONFIG.clear()
    LOGGING_CONFIG.update(original_config)
    
    # Restore logger states
    for name, state in original_loggers.items():
        if name in logging.Logger.manager.loggerDict:
            logger = logging.Logger.manager.loggerDict[name]
            if isinstance(logger, logging.Logger):
                logger.setLevel(state['level'])
                logger.handlers = state['handlers']
                logger.propagate = state['propagate']


class TestRunCommand:
    """Test the RunCommand class"""

    def test_run_command_init(self):
        """Test RunCommand initialization"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ) as mock_run_process:

            def setup_singleton(app_path: str):
                GrpcAPI()

            mock_load_app.side_effect = setup_singleton

            cmd = RunCommand("test_app:app", None)

            assert cmd.command_name == "run"
            assert cmd.app_path == "test_app:app"
            assert isinstance(cmd.app, GrpcAPI)

            mock_load_app.assert_called_once_with("test_app:app")
            mock_run_process.assert_called_once()

    def test_run_command_with_settings(self):
        """Test RunCommand with settings file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"host": "0.0.0.0", "port": 8080}')
            settings_path = f.name

        try:
            with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
                "grpcAPI.commands.command.run_process_service"
            ), patch(
                "grpcAPI.commands.command.load_file_by_extension"
            ) as mock_load_file:

                mock_load_file.return_value = {"host": "0.0.0.0", "port": 8080}

                def setup_singleton(app_path: str):
                    GrpcAPI()

                mock_load_app.side_effect = setup_singleton

                cmd = RunCommand("test_app:app", settings_path)

                assert cmd.settings_path == settings_path
                mock_load_file.assert_called_once()
        finally:
            Path(settings_path).unlink()

    @pytest.mark.asyncio
    async def test_run_command_execution_flow(self, functional_service: APIService):
        """Test RunCommand.run() method without actually starting server"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ):

            def setup_singleton(app_path: str):
                app = GrpcAPI()
                app.add_service(functional_service)

            mock_load_app.side_effect = setup_singleton

            cmd = RunCommand("test_app:app", None)

            # Mock all the server-related operations
            with patch("grpcAPI.commands.run.make_protos") as mock_make_protos, patch(
                "grpcAPI.commands.run.make_server"
            ) as mock_make_server, patch(
                "grpcAPI.commands.run.make_plugin"
            ) as mock_make_plugin, patch(
                "grpcAPI.commands.run.add_to_server"
            ) as mock_add_to_server, patch(
                "grpcAPI.commands.run.get_host_port"
            ) as mock_get_host_port:

                # Setup mocks
                mock_server = Mock()
                mock_server.add_insecure_port = Mock(return_value=50051)
                mock_server.register_plugin = Mock()
                mock_server.start = AsyncMock()
                mock_server.wait_for_termination = AsyncMock()

                mock_make_server.return_value = mock_server
                mock_make_protos.return_value = []
                mock_make_plugin.return_value = []
                mock_get_host_port.return_value = ("localhost", 50051)

                # Mock AsyncExitStack to avoid actual lifespan management
                with patch("grpcAPI.commands.run.AsyncExitStack") as mock_stack:
                    mock_stack_instance = AsyncMock()
                    mock_stack.return_value.__aenter__ = AsyncMock(
                        return_value=mock_stack_instance
                    )
                    mock_stack.return_value.__aexit__ = AsyncMock(return_value=None)
                    mock_stack_instance.enter_async_context = AsyncMock()

                    # Execute the run command
                    await cmd.run()

                    # Verify the execution flow
                    mock_make_protos.assert_called_once_with(cmd.app.services)
                    mock_make_server.assert_called_once()
                    mock_get_host_port.assert_called_once()
                    mock_server.add_insecure_port.assert_called_once_with(
                        "localhost:50051"
                    )
                    mock_add_to_server.assert_called_once()
                    mock_server.start.assert_called_once()
                    mock_server.wait_for_termination.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_command_with_plugins(self, functional_service: APIService):
        """Test RunCommand with plugins enabled"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ), patch("grpcAPI.commands.command.load_file_by_extension") as mock_load_file:

            mock_load_file.return_value = {
                "plugins": {"health": {}, "reflection": {"enabled": True}}
            }

            def setup_singleton(app_path: str):
                app = GrpcAPI()
                app.add_service(functional_service)

            mock_load_app.side_effect = setup_singleton

            cmd = RunCommand("test_app:app", "settings.json")

            with patch("grpcAPI.commands.run.make_protos") as mock_make_protos, patch(
                "grpcAPI.commands.run.make_server"
            ) as mock_make_server, patch(
                "grpcAPI.commands.run.make_plugin"
            ) as mock_make_plugin, patch(
                "grpcAPI.commands.run.add_to_server"
            ) as mock_add_to_server, patch(
                "grpcAPI.commands.run.get_host_port"
            ) as mock_get_host_port:

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
                mock_get_host_port.return_value = ("localhost", 50051)

                with patch("grpcAPI.commands.run.AsyncExitStack") as mock_stack:
                    mock_stack_instance = AsyncMock()
                    mock_stack.return_value.__aenter__ = AsyncMock(
                        return_value=mock_stack_instance
                    )
                    mock_stack.return_value.__aexit__ = AsyncMock(return_value=None)
                    mock_stack_instance.enter_async_context = AsyncMock()

                    await cmd.run()

                    # Verify plugins were created and registered
                    assert mock_make_plugin.call_count == 2  # health and reflection
                    mock_server.register_plugin.assert_called()

    @pytest.mark.asyncio
    async def test_run_command_with_custom_server(self, functional_service: APIService):
        """Test RunCommand when app already has a server"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ):

            def setup_singleton(app_path: str):
                app = GrpcAPI()
                app.add_service(functional_service)
                # Set a custom server
                app.server = Mock()

            mock_load_app.side_effect = setup_singleton

            cmd = RunCommand("test_app:app", None)

            with patch("grpcAPI.commands.run.make_protos") as mock_make_protos, patch(
                "grpcAPI.commands.run.ServerWrapper"
            ) as mock_server_wrapper, patch(
                "grpcAPI.commands.run.make_server"
            ) as mock_make_server, patch(
                "grpcAPI.commands.run.add_to_server"
            ) as mock_add_to_server, patch(
                "grpcAPI.commands.run.get_host_port"
            ) as mock_get_host_port:

                mock_server = Mock()
                mock_server.add_insecure_port = Mock(return_value=50051)
                mock_server.register_plugin = Mock()
                mock_server.start = AsyncMock()
                mock_server.wait_for_termination = AsyncMock()

                mock_server_wrapper.return_value = mock_server
                mock_make_protos.return_value = []
                mock_get_host_port.return_value = ("localhost", 50051)

                with patch("grpcAPI.commands.run.AsyncExitStack") as mock_stack:
                    mock_stack_instance = AsyncMock()
                    mock_stack.return_value.__aenter__ = AsyncMock(
                        return_value=mock_stack_instance
                    )
                    mock_stack.return_value.__aexit__ = AsyncMock(return_value=None)
                    mock_stack_instance.enter_async_context = AsyncMock()

                    await cmd.run()

                    # Verify custom server path was taken
                    mock_server_wrapper.assert_called_once_with(cmd.app.server)
                    mock_make_server.assert_not_called()

    def test_singleton_behavior_across_commands(self, functional_service: APIService):
        """Test that multiple RunCommand instances share the same GrpcAPI singleton"""
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

            cmd1 = RunCommand("test_app:app", None)
            cmd2 = RunCommand("another_app:app", None)

            assert cmd1.app is cmd2.app
