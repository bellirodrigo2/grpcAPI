# test_integration.py - Fixed version with appropriate mock
from unittest.mock import AsyncMock, Mock, patch

import pytest

from grpcAPI.server import ServerWrapper
from grpcAPI.server_plugins.plugins.health_check import HealthCheckPlugin
from grpcAPI.server_plugins.plugins.reflection import ReflectionPlugin


class TestIntegration:

    @pytest.fixture
    def mock_grpc_server(self) -> Mock:
        """Mock of internal gRPC server."""
        server = Mock()  # Remover spec para permitir qualquer atributo
        server.add_registered_method_handlers = Mock()
        server.start = AsyncMock()
        server.stop = AsyncMock()
        return server

    @pytest.fixture
    def mock_server_wrapper(self, mock_grpc_server) -> Mock:
        """Mock of ServerWrapper that has server property."""
        wrapper = Mock()
        wrapper.server = mock_grpc_server  # FIX: Adicionar propriedade server
        wrapper.plugins = []
        return wrapper

    @pytest.fixture
    def server_wrapper(self, mock_grpc_server):
        """Create a real ServerWrapper with mocked grpc server."""
        return ServerWrapper(mock_grpc_server)

    @pytest.mark.asyncio
    async def test_server_with_plugins_lifecycle(
        self, server_wrapper: ServerWrapper
    ) -> None:
        health_plugin = HealthCheckPlugin(grace=0.1)
        reflection_plugin = ReflectionPlugin()

        server_wrapper.register_plugin(health_plugin)
        server_wrapper.register_plugin(reflection_plugin)

        # Simulate adding a service
        name = "TestService"

        with patch(
            "grpc_reflection.v1alpha.reflection.enable_server_reflection"
        ), patch(
            "grpcAPI.server_plugins.plugins.health_check.health_pb2_grpc.add_HealthServicer_to_server"
        ):

            server_wrapper.add_registered_method_handlers(name, {})

            # Verify both plugins were called
            assert "TestService" in health_plugin._services_set
            assert "TestService" in reflection_plugin._services

        # Test server lifecycle
        await server_wrapper.start()
        server_wrapper.server.start.assert_called_once()

        # Test graceful shutdown
        await server_wrapper.stop(grace=1.0)

        # Verify cleanup was called
        server_wrapper.server.stop.assert_called_once_with(1.0)

    @pytest.mark.asyncio
    async def test_health_plugin_lifecycle(self, mock_server_wrapper: Mock) -> None:
        """Specific test of health plugin lifecycle."""
        health_plugin = HealthCheckPlugin(grace=0.1)

        # Simulate registration
        with patch(
            "grpcAPI.server_plugins.plugins.health_check.health_pb2_grpc.add_HealthServicer_to_server"
        ):
            health_plugin.on_register(mock_server_wrapper)

        # Check state after registration
        state_after_register = health_plugin.state
        assert state_after_register["name"] == "health_check"
        assert "" in state_after_register["services"]  # Serviço raiz

        # Simulate service addition
        health_plugin.on_add_service("TestService", {}, mock_server_wrapper)
        assert "TestService" in health_plugin._services_set

        # Testar graceful shutdown
        with patch("asyncio.sleep") as mock_sleep:
            await health_plugin.on_stop()
            mock_sleep.assert_called_with(0.1)  # grace do plugin

    @pytest.mark.asyncio
    async def test_reflection_plugin_lifecycle(self, mock_server_wrapper: Mock) -> None:
        """Specific test of reflection plugin lifecycle."""
        reflection_plugin = ReflectionPlugin()

        # Check initial state
        initial_state = reflection_plugin.state
        assert initial_state["name"] == "reflection"
        assert len(initial_state["services"]) == 0

        # Add multiple services
        with patch(
            "grpc_reflection.v1alpha.reflection.enable_server_reflection"
        ) as mock_reflection:
            services = ["ServiceA", "ServiceB", "ServiceC"]

            for service in services:
                reflection_plugin.on_add_service(service, {}, mock_server_wrapper)

            # Check that reflection was called for each service
            assert mock_reflection.call_count == len(services)
            for service in services:
                mock_reflection.assert_any_call((service,), mock_server_wrapper.server)
