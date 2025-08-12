import os
from datetime import datetime
from unittest.mock import Mock, patch

import grpc
import pytest

from grpcAPI.logger import LOGGING_CONFIG
from grpcAPI.server import ServerWrapper
from grpcAPI.server_plugins.plugins.server_logger import ServerLoggerPlugin, add_logger


class TestAddLogger:

    @patch(
        "grpcAPI.server_plugins.plugins.server_logger.LOGGING_CONFIG",
        {
            "loggers": {
                "grpcAPI": {
                    "level": "ERROR",
                    "handlers": ["console"],
                    "propagate": False,
                }
            }
        },
    )
    @patch("logging.config.dictConfig")
    def test_add_logger_new_logger(self, mock_dict_config):
        level, handlers, propagate = add_logger(
            "test_logger", level="DEBUG", handlers=["file"], propagate=True
        )

        assert level == "DEBUG"
        assert "console" in handlers
        assert "server_logger_handler" in handlers
        assert propagate
        mock_dict_config.assert_called_once()

    @patch(
        "grpcAPI.server_plugins.plugins.server_logger.LOGGING_CONFIG",
        {
            "loggers": {
                "existing_logger": {
                    "level": "INFO",
                    "handlers": ["console"],
                    "propagate": False,
                }
            }
        },
    )
    def test_add_logger_existing_logger(self):
        level, handlers, propagate = add_logger("existing_logger")

        assert level == "INFO"
        assert handlers == ["console"]
        assert not propagate

    @patch("grpcAPI.server_plugins.plugins.server_logger.LOGGING_CONFIG", {})
    @patch("logging.config.dictConfig")
    def test_add_logger_no_template(self, mock_dict_config):
        level, handlers, propagate = add_logger("new_logger", level="WARNING")

        assert level == "WARNING"
        assert handlers == ["console"]  # default
        mock_dict_config.assert_called_once()


class TestServerLoggerPlugin:

    @pytest.fixture
    def mock_server(self):
        mock_grpc_server = Mock(spec=grpc.aio.Server)
        server = ServerWrapper(mock_grpc_server, [])
        return server

    @pytest.fixture
    def plugin_kwargs(self):
        return {"level": "DEBUG", "handlers": ["console", "file"], "propagate": False}

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    def test_init(self, mock_get_logger, mock_add_logger, plugin_kwargs):
        mock_add_logger.return_value = ("DEBUG", ["console", "file"], False)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        plugin = ServerLoggerPlugin(**plugin_kwargs)

        mock_add_logger.assert_called_once_with("server_logger_plugin", **plugin_kwargs)
        mock_get_logger.assert_called_once_with("server_logger_plugin")

        assert plugin.level == "DEBUG"
        assert plugin.handlers == ["console", "file"]
        assert not plugin.propagate
        assert plugin._logger == mock_logger
        assert plugin._services == {}
        assert plugin._server_starts == []
        assert plugin._server_stops == []
        assert not plugin._wait_for_termination

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    def test_plugin_name(self, mock_get_logger, mock_add_logger):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        plugin = ServerLoggerPlugin()

        assert plugin.plugin_name == "server_logger"

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    def test_state(self, mock_get_logger, mock_add_logger):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        plugin = ServerLoggerPlugin()
        plugin._services = {"TestService": ["method1", "method2"]}

        state = plugin.state

        assert state["services"] == {"TestService": ["method1", "method2"]}
        assert state["logger"] == mock_logger
        assert state["logger_config"]["level"] == "INFO"
        assert state["logger_config"]["handlers"] == ["console"]
        assert state["logger_config"]["propagate"]

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    def test_on_register(self, mock_get_logger, mock_add_logger, mock_server):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        plugin = ServerLoggerPlugin()

        # Should not raise any exception
        plugin.on_register(mock_server)

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    def test_on_add_service(self, mock_get_logger, mock_add_logger, mock_server):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        plugin = ServerLoggerPlugin()
        methods = ["method1", "method2"]

        plugin.on_add_service("TestService", methods, mock_server)

        assert plugin._services["TestService"] == methods
        mock_logger.info.assert_called_once_with(
            "Service 'TestService' added to server."
        )
        mock_logger.debug.assert_called_once_with("Methods: ['method1', 'method2']")

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    def test_on_add_port_insecure(self, mock_get_logger, mock_add_logger):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        plugin = ServerLoggerPlugin()

        plugin.on_add_port("localhost:50051", None)

        mock_logger.info.assert_called_once_with(
            "Insecure port 'localhost:50051' added to server."
        )

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    def test_on_add_port_secure(self, mock_get_logger, mock_add_logger):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        plugin = ServerLoggerPlugin()
        mock_credentials = Mock(spec=grpc.ServerCredentials)

        plugin.on_add_port("localhost:50051", mock_credentials)

        mock_logger.info.assert_called_once_with(
            "Secure port 'localhost:50051' added to server."
        )

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.datetime")
    @pytest.mark.asyncio
    async def test_on_start(
        self, mock_datetime, mock_get_logger, mock_add_logger, mock_server
    ):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        start_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = start_time

        plugin = ServerLoggerPlugin()
        plugin._services = {"Service1": ["method1"], "Service2": ["method2", "method3"]}

        # Add some mock plugins to server
        mock_plugin1 = Mock()
        mock_plugin1.plugin_name = "plugin1"
        mock_plugin2 = Mock()
        mock_plugin2.plugin_name = "plugin2"
        mock_server.plugins = [mock_plugin1, mock_plugin2]

        await plugin.on_start(mock_server)

        assert plugin._server_starts == [start_time]
        mock_logger.info.assert_called_once_with(
            "Server started, 2 plugins, 2 services."
        )
        mock_logger.debug.assert_any_call("Server plugins: ['plugin1', 'plugin2']")

        # Check services debug log
        expected_services = "Service1:\n method1\nService2:\n method2, method3\n"
        mock_logger.debug.assert_any_call(f"Registered services:\n{expected_services}")

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    @pytest.mark.asyncio
    async def test_on_wait_for_termination(self, mock_get_logger, mock_add_logger):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        plugin = ServerLoggerPlugin()

        await plugin.on_wait_for_termination(timeout=30.0)

        assert plugin._wait_for_termination
        mock_logger.info.assert_called_once_with(
            "Server is waiting for termination: timeout 30.0."
        )

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.datetime")
    @pytest.mark.asyncio
    async def test_on_stop(self, mock_datetime, mock_get_logger, mock_add_logger):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        start_time = datetime(2023, 1, 1, 12, 0, 0)
        stop_time = datetime(2023, 1, 1, 12, 30, 0)
        mock_datetime.now.return_value = stop_time

        plugin = ServerLoggerPlugin()
        plugin._server_starts = [start_time]
        plugin._wait_for_termination = True

        await plugin.on_stop()

        assert plugin._server_stops == [stop_time]
        assert not plugin._wait_for_termination

        mock_logger.info.assert_called_once_with("Server stopped.")
        mock_logger.debug.assert_any_call("Waiting for termination: 'True' ")

        expected_duration = stop_time - start_time
        mock_logger.debug.assert_any_call(
            f"Server last start {start_time}. Runned for {expected_duration}."
        )

    @patch("grpcAPI.server_plugins.plugins.server_logger.add_logger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.getLogger")
    @patch("grpcAPI.server_plugins.plugins.server_logger.datetime")
    @pytest.mark.asyncio
    async def test_multiple_start_stop_cycles(
        self, mock_datetime, mock_get_logger, mock_add_logger, mock_server
    ):
        mock_add_logger.return_value = ("INFO", ["console"], True)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        plugin = ServerLoggerPlugin()

        # First cycle
        start_time1 = datetime(2023, 1, 1, 12, 0, 0)
        stop_time1 = datetime(2023, 1, 1, 12, 30, 0)

        mock_datetime.now.return_value = start_time1
        await plugin.on_start(mock_server)

        mock_datetime.now.return_value = stop_time1
        await plugin.on_stop()

        # Second cycle
        start_time2 = datetime(2023, 1, 1, 13, 0, 0)
        stop_time2 = datetime(2023, 1, 1, 13, 45, 0)

        mock_datetime.now.return_value = start_time2
        await plugin.on_start(mock_server)

        mock_datetime.now.return_value = stop_time2
        await plugin.on_stop()

        assert plugin._server_starts == [start_time1, start_time2]
        assert plugin._server_stops == [stop_time1, stop_time2]

    @patch("grpcAPI.server_plugins.plugins.server_logger.loader")
    def test_register(self, mock_loader):
        from grpcAPI.server_plugins.plugins.server_logger import register

        register()

        mock_loader.register.assert_called_once_with(
            "server_logger", ServerLoggerPlugin
        )


class TestServerLoggerFileHandler:
    """Additional tests for log file functionality"""

    def setup_method(self):
        """Reset LOGGING_CONFIG before each test"""
        import copy

        self.original_config = copy.deepcopy(LOGGING_CONFIG)

    def teardown_method(self):
        """Restore original config after each test"""
        LOGGING_CONFIG.clear()
        LOGGING_CONFIG.update(self.original_config)

    def test_add_logger_with_filename_creates_file_handler(self):
        """Test if add_logger creates file handler when filename is provided"""
        import uuid

        filename = f"/tmp/test_{uuid.uuid4().hex[:8]}.log"

        try:
            level, handlers, propagate = add_logger(
                "test_logger", filename=filename, handlers=["file", "console"]
            )

            # Check if handler was created in global LOGGING_CONFIG
            assert "server_logger_handler" in LOGGING_CONFIG["handlers"]

            # Check if filename was configured correctly
            file_handler = LOGGING_CONFIG["handlers"]["server_logger_handler"]
            assert file_handler["filename"] == filename

            # Check if 'file' was replaced by 'server_logger_handler'
            assert "server_logger_handler" in handlers
            assert "file" not in handlers
            assert "console" in handlers

        finally:
            if os.path.exists(filename):
                try:
                    os.unlink(filename)
                except (OSError, PermissionError):
                    pass

    def test_add_logger_without_filename_no_file_handler(self):
        """Test if add_logger does not create file handler when filename is not provided"""
        # Clear any existing handler
        LOGGING_CONFIG.setdefault("handlers", {}).pop("server_logger_handler", None)

        level, handlers, propagate = add_logger("test_logger", handlers=["console"])

        # Should not create file handler
        assert "server_logger_handler" not in LOGGING_CONFIG.get("handlers", {})
        assert "console" in handlers
        assert "file" not in handlers

    def test_plugin_state_includes_logger_config(self):
        """Test if plugin state includes logger configuration"""
        plugin = ServerLoggerPlugin(level="INFO", handlers=["console"])

        state = plugin.state
        assert "logger_config" in state
        assert state["logger_config"]["level"] == "INFO"
        assert state["logger_config"]["handlers"] == ["console"]
        assert state["logger_config"]["propagate"] is True

    @patch("logging.config.dictConfig")
    def test_multiple_file_handlers_different_names(self, mock_dict_config):
        """Test creation of multiple file handlers with different names"""
        # Setup handler base
        LOGGING_CONFIG.setdefault("handlers", {})["file"] = {
            "class": "logging.FileHandler",
            "level": "INFO",
        }

        filename1 = "/tmp/test1.log"
        filename2 = "/tmp/test2.log"

        # First logger
        add_logger("logger1", filename=filename1, handlers=["file"])

        # Second logger - should override previous handler
        add_logger("logger2", filename=filename2, handlers=["file"])

        # Verifica se o handler foi atualizado com o novo filename
        file_handler = LOGGING_CONFIG["handlers"]["server_logger_handler"]
        assert file_handler["filename"] == filename2

        # Verifica se dictConfig foi chamado
        assert mock_dict_config.call_count == 2

    def test_add_logger_with_custom_propagate_setting(self):
        """Test custom propagate configuration"""
        level, handlers, propagate = add_logger(
            "test_logger", filename="/tmp/test.log", handlers=["file"], propagate=False
        )

        assert propagate is False
        assert LOGGING_CONFIG["loggers"]["test_logger"]["propagate"] is False

    @patch("logging.config.dictConfig")
    def test_logging_config_called_when_adding_file_handler(self, mock_dict_config):
        """Test if logging.config.dictConfig is called when file handler is added"""
        add_logger("test_logger", filename="/tmp/test.log", handlers=["file"])

        # Check if dictConfig was called with updated configuration
        mock_dict_config.assert_called_once_with(LOGGING_CONFIG)

        # Check if passed configuration includes new handler
        call_args = mock_dict_config.call_args[0][0]
        assert "server_logger_handler" in call_args["handlers"]

    def test_existing_logger_name_returns_existing_config(self):
        """Test if existing logger returns configuration without modification"""
        # Limpar qualquer handler residual
        LOGGING_CONFIG.setdefault("handlers", {}).pop("server_logger_handler", None)

        # Setup: existing logger
        existing_config = {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        }
        LOGGING_CONFIG.setdefault("loggers", {})["existing_logger"] = existing_config

        level, handlers, propagate = add_logger(
            "existing_logger",
            filename="/tmp/should_not_create.log",  # Should not create file
        )

        # Should return existing configuration
        assert level == "WARNING"
        assert handlers == ["console"]
        assert propagate is False

        # Should not create new handler
        assert "server_logger_handler" not in LOGGING_CONFIG.get("handlers", {})


class TestServerLoggerPluginIntegration:
    """Testes de integração simplificados"""

    def test_plugin_basic_functionality(self):
        """Teste básico de funcionalidade do plugin"""
        plugin = ServerLoggerPlugin(level="INFO", handlers=["console"])

        # Check basic properties
        assert plugin.plugin_name == "server_logger"
        assert plugin.level == "INFO"
        assert "console" in plugin.handlers

        # Check logger
        assert plugin._logger.name == "server_logger_plugin"

        # Check state
        state = plugin.state
        assert "services" in state
        assert "logger" in state
        assert "logger_config" in state
