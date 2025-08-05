from unittest.mock import AsyncMock, Mock, patch

import grpc
import pytest

from grpcAPI.server import ServerWrapper, make_server
from tests.plugins.helper import MockPlugin


class TestServerWrapper:

    @pytest.fixture
    def mock_grpc_server(self) -> None:
        server = Mock(spec=grpc.aio.Server)
        server.add_generic_rpc_handlers = Mock()
        server.add_insecure_port = Mock(return_value=50051)
        server.add_secure_port = Mock(return_value=50052)
        server.start = AsyncMock()
        server.stop = AsyncMock()
        server.wait_for_termination = AsyncMock(return_value=True)
        server.add_registered_method_handlers = Mock()
        return server

    @pytest.fixture
    def server_wrapper(self, mock_grpc_server):
        return ServerWrapper(mock_grpc_server)

    def test_init(self, mock_grpc_server):
        # Test without plugins
        wrapper = ServerWrapper(mock_grpc_server)
        assert wrapper.server == mock_grpc_server
        assert wrapper.plugins == []

        # Test with plugins
        plugin = MockPlugin()
        wrapper = ServerWrapper(mock_grpc_server, [plugin])
        assert len(wrapper.plugins) == 1
        assert wrapper.plugins[0] == plugin

    def test_register_plugin(self, server_wrapper: ServerWrapper) -> None:
        plugin = MockPlugin()
        server_wrapper.register_plugin(plugin)

        assert plugin in server_wrapper.plugins
        assert plugin.on_register_called

    def test_add_generic_rpc_handlers_with_handlers(
        self, server_wrapper: ServerWrapper
    ) -> None:
        plugin = MockPlugin()
        server_wrapper.register_plugin(plugin)

        # Mock handler with _name attribute
        handler = Mock()
        handler._name = "TestService"

        handlers = [handler]
        server_wrapper.add_generic_rpc_handlers(handlers)

        # Verify plugin was called
        assert plugin.on_add_service_called
        assert "TestService" in plugin.services

        # Verify server method was called
        server_wrapper.server.add_generic_rpc_handlers.assert_called_once_with(handlers)

    def test_add_generic_rpc_handlers_without_name(
        self, server_wrapper: ServerWrapper
    ) -> None:
        plugin = MockPlugin()
        server_wrapper.register_plugin(plugin)

        # Mock handler without _name attribute
        handler = Mock(spec=[])  # spec=[] means no attributes
        handlers = [handler]

        server_wrapper.add_generic_rpc_handlers(handlers)

        # Should use 'unknown_service' as fallback
        assert plugin.on_add_service_called
        assert "unknown_service" in plugin.services

    def test_add_generic_rpc_handlers_empty_list(
        self, server_wrapper: ServerWrapper
    ) -> None:
        plugin = MockPlugin()
        server_wrapper.register_plugin(plugin)

        server_wrapper.add_generic_rpc_handlers([])

        # Plugin should not be called for empty handlers
        assert not plugin.on_add_service_called
        server_wrapper.server.add_generic_rpc_handlers.assert_called_once_with([])

    def test_add_insecure_port(self, server_wrapper: ServerWrapper) -> None:
        result = server_wrapper.add_insecure_port("localhost:50051")
        assert result == 50051
        server_wrapper.server.add_insecure_port.assert_called_once_with(
            "localhost:50051"
        )

    def test_add_secure_port(self, server_wrapper: ServerWrapper) -> None:
        credentials = Mock(spec=grpc.ServerCredentials)
        result = server_wrapper.add_secure_port("localhost:50052", credentials)
        assert result == 50052
        server_wrapper.server.add_secure_port.assert_called_once_with(
            "localhost:50052", credentials
        )

    @pytest.mark.asyncio
    async def test_start_without_lifespan(self, server_wrapper: ServerWrapper) -> None:
        await server_wrapper.start()
        server_wrapper.server.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_with_lifespan(self, server_wrapper: ServerWrapper) -> None:
        lifespan_called = False

        async def mock_lifespan(server):
            nonlocal lifespan_called
            lifespan_called = True
            yield

        await server_wrapper.start(lifespan=mock_lifespan)

        assert lifespan_called
        server_wrapper.server.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_calls_plugin_cleanup(
        self, server_wrapper: ServerWrapper
    ) -> None:
        plugin = MockPlugin()
        server_wrapper.register_plugin(plugin)

        await server_wrapper.stop(grace=1.0)

        assert plugin.on_stop_called
        server_wrapper.server.stop.assert_called_once_with(1.0)

    @pytest.mark.asyncio
    async def test_stop_without_plugin_cleanup(
        self, server_wrapper: ServerWrapper
    ) -> None:
        # Plugin without on_stop method
        plugin = Mock(spec=[])  # No on_stop method
        server_wrapper.plugins.append(plugin)

        # Should not raise error
        await server_wrapper.stop(grace=1.0)
        server_wrapper.server.stop.assert_called_once_with(1.0)

    @pytest.mark.asyncio
    async def test_wait_for_termination(self, server_wrapper: ServerWrapper) -> None:
        result = await server_wrapper.wait_for_termination(timeout=5.0)
        assert result is True
        server_wrapper.server.wait_for_termination.assert_called_once_with(5.0)

    def test_add_registered_method_handlers(
        self, server_wrapper: ServerWrapper
    ) -> None:
        handlers = {"method": Mock()}
        server_wrapper.add_registered_method_handlers("TestService", handlers)
        server_wrapper.server.add_registered_method_handlers.assert_called_once_with(
            "TestService", handlers
        )


def test_make_server() -> None:
    server_settings = {"grpc.keepalive_time_ms": 30000}
    middlewares = []

    with patch("grpc.aio.server") as mock_grpc_server:
        mock_server_instance = Mock()
        mock_grpc_server.return_value = mock_server_instance

        wrapper = make_server(server_settings, middlewares)

        # Verify grpc.aio.server was called with correct parameters
        mock_grpc_server.assert_called_once_with(
            interceptors=middlewares, options=server_settings.items()
        )

        assert isinstance(wrapper, ServerWrapper)
        assert wrapper.server == mock_server_instance
        assert wrapper.plugins == []
