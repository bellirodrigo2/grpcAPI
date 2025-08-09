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
        assert propagate == True
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
        assert propagate == False

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
        assert plugin.propagate == False
        assert plugin._logger == mock_logger
        assert plugin._services == {}
        assert plugin._server_starts == []
        assert plugin._server_stops == []
        assert plugin._wait_for_termination == False

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
        assert state["logger_config"]["propagate"] == True

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

        assert plugin._wait_for_termination == True
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
        assert plugin._wait_for_termination == False

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
    """Testes adicionais para funcionalidade de arquivo de log"""

    def setup_method(self):
        """Reset LOGGING_CONFIG antes de cada teste"""
        import copy

        self.original_config = copy.deepcopy(LOGGING_CONFIG)

    def teardown_method(self):
        """Restore original config após cada teste"""
        LOGGING_CONFIG.clear()
        LOGGING_CONFIG.update(self.original_config)

    def test_add_logger_with_filename_creates_file_handler(self):
        """Testa se add_logger cria handler de arquivo quando filename é fornecido"""
        import uuid

        filename = f"/tmp/test_{uuid.uuid4().hex[:8]}.log"

        try:
            level, handlers, propagate = add_logger(
                "test_logger", filename=filename, handlers=["file", "console"]
            )

            # Verifica se o handler foi criado no LOGGING_CONFIG global
            assert "server_logger_handler" in LOGGING_CONFIG["handlers"]

            # Verifica se o filename foi configurado corretamente
            file_handler = LOGGING_CONFIG["handlers"]["server_logger_handler"]
            assert file_handler["filename"] == filename

            # Verifica se 'file' foi substituído por 'server_logger_handler'
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
        """Testa se add_logger não cria handler de arquivo quando filename não é fornecido"""
        # Limpar qualquer handler existente
        LOGGING_CONFIG.setdefault("handlers", {}).pop("server_logger_handler", None)

        level, handlers, propagate = add_logger("test_logger", handlers=["console"])

        # Não deve criar o handler de arquivo
        assert "server_logger_handler" not in LOGGING_CONFIG.get("handlers", {})
        assert "console" in handlers
        assert "file" not in handlers

    def test_plugin_state_includes_logger_config(self):
        """Testa se o state do plugin inclui configuração do logger"""
        plugin = ServerLoggerPlugin(level="INFO", handlers=["console"])

        state = plugin.state
        assert "logger_config" in state
        assert state["logger_config"]["level"] == "INFO"
        assert state["logger_config"]["handlers"] == ["console"]
        assert state["logger_config"]["propagate"] is True

    @patch("logging.config.dictConfig")
    def test_multiple_file_handlers_different_names(self, mock_dict_config):
        """Testa criação de múltiplos handlers de arquivo com nomes diferentes"""
        # Setup handler base
        LOGGING_CONFIG.setdefault("handlers", {})["file"] = {
            "class": "logging.FileHandler",
            "level": "INFO",
        }

        filename1 = "/tmp/test1.log"
        filename2 = "/tmp/test2.log"

        # Primeiro logger
        add_logger("logger1", filename=filename1, handlers=["file"])

        # Segundo logger - deve sobrescrever o handler anterior
        add_logger("logger2", filename=filename2, handlers=["file"])

        # Verifica se o handler foi atualizado com o novo filename
        file_handler = LOGGING_CONFIG["handlers"]["server_logger_handler"]
        assert file_handler["filename"] == filename2

        # Verifica se dictConfig foi chamado
        assert mock_dict_config.call_count == 2

    def test_add_logger_with_custom_propagate_setting(self):
        """Testa configuração personalizada de propagate"""
        level, handlers, propagate = add_logger(
            "test_logger", filename="/tmp/test.log", handlers=["file"], propagate=False
        )

        assert propagate is False
        assert LOGGING_CONFIG["loggers"]["test_logger"]["propagate"] is False

    @patch("logging.config.dictConfig")
    def test_logging_config_called_when_adding_file_handler(self, mock_dict_config):
        """Testa se logging.config.dictConfig é chamado quando handler de arquivo é adicionado"""
        add_logger("test_logger", filename="/tmp/test.log", handlers=["file"])

        # Verifica se dictConfig foi chamado com a configuração atualizada
        mock_dict_config.assert_called_once_with(LOGGING_CONFIG)

        # Verifica se a configuração passada inclui o novo handler
        call_args = mock_dict_config.call_args[0][0]
        assert "server_logger_handler" in call_args["handlers"]

    def test_existing_logger_name_returns_existing_config(self):
        """Testa se logger existente retorna configuração sem modificar"""
        # Limpar qualquer handler residual
        LOGGING_CONFIG.setdefault("handlers", {}).pop("server_logger_handler", None)

        # Setup: logger existente
        existing_config = {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        }
        LOGGING_CONFIG.setdefault("loggers", {})["existing_logger"] = existing_config

        level, handlers, propagate = add_logger(
            "existing_logger",
            filename="/tmp/should_not_create.log",  # Não deve criar arquivo
        )

        # Deve retornar configuração existente
        assert level == "WARNING"
        assert handlers == ["console"]
        assert propagate is False

        # Não deve criar novo handler
        assert "server_logger_handler" not in LOGGING_CONFIG.get("handlers", {})


class TestServerLoggerPluginIntegration:
    """Testes de integração simplificados"""

    def test_plugin_basic_functionality(self):
        """Teste básico de funcionalidade do plugin"""
        plugin = ServerLoggerPlugin(level="INFO", handlers=["console"])

        # Verifica propriedades básicas
        assert plugin.plugin_name == "server_logger"
        assert plugin.level == "INFO"
        assert "console" in plugin.handlers

        # Verifica logger
        assert plugin._logger.name == "server_logger_plugin"

        # Verifica state
        state = plugin.state
        assert "services" in state
        assert "logger" in state
        assert "logger_config" in state
