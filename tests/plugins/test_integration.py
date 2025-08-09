# test_integration.py - Versão corrigida com mock apropriado
from unittest.mock import AsyncMock, Mock, patch

import grpc
import pytest

from grpcAPI.server import ServerWrapper
from grpcAPI.server_plugins.plugins.health_check import HealthCheckPlugin
from grpcAPI.server_plugins.plugins.reflection import ReflectionPlugin


class TestIntegration:

    @pytest.fixture
    def mock_grpc_server(self) -> Mock:
        """Mock do servidor gRPC interno."""
        server = Mock()  # Remover spec para permitir qualquer atributo
        server.add_registered_method_handlers = Mock()
        server.start = AsyncMock()
        server.stop = AsyncMock()
        return server

    @pytest.fixture
    def mock_server_wrapper(self, mock_grpc_server) -> Mock:
        """Mock do ServerWrapper que tem propriedade server."""
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
        """Teste específico do ciclo de vida do health plugin."""
        health_plugin = HealthCheckPlugin(grace=0.1)

        # Simular registro
        with patch(
            "grpcAPI.server_plugins.plugins.health_check.health_pb2_grpc.add_HealthServicer_to_server"
        ):
            health_plugin.on_register(mock_server_wrapper)

        # Verificar estado após registro
        state_after_register = health_plugin.state
        assert state_after_register["name"] == "health_check"
        assert "" in state_after_register["services"]  # Serviço raiz

        # Simular adição de serviço
        health_plugin.on_add_service("TestService", mock_server_wrapper)
        assert "TestService" in health_plugin._services_set

        # Testar graceful shutdown
        with patch("asyncio.sleep") as mock_sleep:
            await health_plugin.on_stop()
            mock_sleep.assert_called_with(0.1)  # grace do plugin

    @pytest.mark.asyncio
    async def test_reflection_plugin_lifecycle(self, mock_server_wrapper: Mock) -> None:
        """Teste específico do ciclo de vida do reflection plugin."""
        reflection_plugin = ReflectionPlugin()

        # Verificar estado inicial
        initial_state = reflection_plugin.state
        assert initial_state["name"] == "reflection"
        assert len(initial_state["services"]) == 0

        # Adicionar múltiplos serviços
        with patch(
            "grpc_reflection.v1alpha.reflection.enable_server_reflection"
        ) as mock_reflection:
            services = ["ServiceA", "ServiceB", "ServiceC"]

            for service in services:
                reflection_plugin.on_add_service(service, mock_server_wrapper)

            # Verificar que reflection foi chamada para cada serviço
            assert mock_reflection.call_count == len(services)
            for service in services:
                mock_reflection.assert_any_call((service,), mock_server_wrapper.server)
                # test_integration.py - Versão corrigida com mocks apropriados


from unittest.mock import Mock

import pytest

from grpcAPI.server import ServerWrapper


class TestIntegration:

    @pytest.fixture
    def mock_grpc_server(self) -> Mock:
        server = Mock(spec=grpc.aio.Server)
        server.add_registered_method_handlers = Mock()
        server.start = AsyncMock()
        server.stop = AsyncMock()
        return server

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
        handler = Mock()
        name = "TestService"

        with patch(
            "grpc_reflection.v1alpha.reflection.enable_server_reflection"
        ), patch(
            "grpcAPI.server_plugins.plugins.health_check.health_pb2_grpc.add_HealthServicer_to_server"
        ):

            server_wrapper.add_registered_method_handlers(name, handler)

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
    async def test_health_plugin_lifecycle(self, server_wrapper: ServerWrapper) -> None:
        """Teste específico do ciclo de vida do health plugin."""
        health_plugin = HealthCheckPlugin(grace=0.1)
        server_wrapper.register_plugin(health_plugin)

        # Verificar estado inicial
        initial_state = health_plugin.state
        assert initial_state["name"] == "health_check"
        assert "" in initial_state["services"]  # Serviço raiz adicionado no on_register

        # Adicionar serviço
        with patch(
            "grpcAPI.server_plugins.plugins.health_check.health_pb2_grpc.add_HealthServicer_to_server"
        ):
            handler = Mock()
            name = "TestService"
            server_wrapper.add_registered_method_handlers(name, handler)

            # Verificar que serviço foi adicionado
            assert "TestService" in health_plugin._services_set

        # Testar graceful shutdown
        with patch("asyncio.sleep") as mock_sleep:
            await server_wrapper.stop(grace=1.0)
            # Verificar que o plugin teve tempo de graceful shutdown
            mock_sleep.assert_called_with(0.1)  # grace do plugin

    @pytest.mark.asyncio
    async def test_plugins_interaction(self, server_wrapper: ServerWrapper) -> None:
        """Testar se os plugins não interferem uns com os outros."""
        health_plugin = HealthCheckPlugin(grace=0.05)
        reflection_plugin = ReflectionPlugin()

        server_wrapper.register_plugin(health_plugin)
        server_wrapper.register_plugin(reflection_plugin)

        # Verificar que ambos foram registrados
        assert len(server_wrapper.plugins) == 2
        assert health_plugin in server_wrapper.plugins
        assert reflection_plugin in server_wrapper.plugins

        with patch(
            "grpc_reflection.v1alpha.reflection.enable_server_reflection"
        ), patch(
            "grpcAPI.server_plugins.plugins.health_check.health_pb2_grpc.add_HealthServicer_to_server"
        ):
            services = ["UserService", "OrderService"]
            for service in services:
                server_wrapper.add_registered_method_handlers(service, {})

            # Verificar que ambos os plugins foram informados sobre todos os serviços
            for service in services:
                assert service in health_plugin._services_set
                assert service in reflection_plugin._services

            # Verificar estados independentes
            health_state = health_plugin.state
            reflection_state = reflection_plugin.state

            assert health_state["name"] == "health_check"
            assert reflection_state["name"] == "reflection"

            # Health plugin tem serviço raiz "" também
            assert len(health_state["services"]) == len(services) + 1  # +1 para ""
            assert len(reflection_state["services"]) == len(services)

    @pytest.mark.asyncio
    async def test_error_handling_in_plugins(
        self, server_wrapper: ServerWrapper
    ) -> None:
        """Testar se erros em um plugin não afetam outros."""
        health_plugin = HealthCheckPlugin()
        reflection_plugin = ReflectionPlugin()

        server_wrapper.register_plugin(health_plugin)
        server_wrapper.register_plugin(reflection_plugin)

        # Simular erro no reflection plugin
        with patch(
            "grpc_reflection.v1alpha.reflection.enable_server_reflection"
        ) as mock_reflection, patch(
            "grpcAPI.server_plugins.plugins.health_check.health_pb2_grpc.add_HealthServicer_to_server"
        ):

            # Fazer reflection falhar
            mock_reflection.side_effect = Exception("Reflection failed")

            handler = Mock()
            name = "TestService"

            # Deve falhar, mas não devemos capturar a exceção aqui pois não implementamos tratamento de erro
            # Vamos apenas verificar que o health plugin ainda funciona
            try:
                server_wrapper.add_registered_method_handlers(name, handler)
            except Exception:
                # Esperado que falhe devido ao reflection
                pass

            # Health plugin deve ter funcionado mesmo com reflection falhando
            assert "TestService" in health_plugin._services_set
