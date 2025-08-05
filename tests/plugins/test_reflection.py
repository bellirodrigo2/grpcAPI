from unittest.mock import Mock, patch

import pytest

from grpcAPI.server import ServerWrapper
from grpcAPI.server_plugins.plugins.reflection import ReflectionPlugin


class TestReflectionPlugin:

    @pytest.fixture
    def plugin(self) -> ReflectionPlugin:
        return ReflectionPlugin()

    @pytest.fixture
    def mock_server_wrapper(self) -> Mock:
        """Criar um mock do ServerWrapper."""
        wrapper = Mock(spec=ServerWrapper)
        wrapper.server = Mock()  # Mock do grpc.aio.Server interno
        return wrapper

    def test_init(self, plugin: ReflectionPlugin) -> None:
        assert plugin.plugin_name == "reflection"
        assert len(plugin._services) == 0

    def test_state_property(self, plugin: ReflectionPlugin) -> None:
        plugin._services.add("TestService")
        state = plugin.state

        assert state["name"] == "reflection"
        assert "TestService" in state["services"]

    @patch("grpc_reflection.v1alpha.reflection.enable_server_reflection")
    def test_on_add_service(
        self,
        mock_enable_reflection,
        plugin: ReflectionPlugin,
        mock_server_wrapper: Mock,
    ) -> None:
        plugin.on_add_service("TestService", mock_server_wrapper)

        # Verificar se foi chamado com tupla de service names e o servidor interno
        mock_enable_reflection.assert_called_once_with(
            ("TestService",), mock_server_wrapper.server
        )
        assert "TestService" in plugin._services

    @patch("grpc_reflection.v1alpha.reflection.enable_server_reflection")
    def test_on_add_service_multiple_services(
        self,
        mock_enable_reflection,
        plugin: ReflectionPlugin,
        mock_server_wrapper: Mock,
    ) -> None:
        # Adicionar múltiplos serviços
        plugin.on_add_service("ServiceA", mock_server_wrapper)
        plugin.on_add_service("ServiceB", mock_server_wrapper)

        # Verificar se ambos foram chamados
        assert mock_enable_reflection.call_count == 2
        mock_enable_reflection.assert_any_call(
            ("ServiceA",), mock_server_wrapper.server
        )
        mock_enable_reflection.assert_any_call(
            ("ServiceB",), mock_server_wrapper.server
        )

        # Verificar se ambos estão no state
        assert "ServiceA" in plugin._services
        assert "ServiceB" in plugin._services
        assert len(plugin._services) == 2

    def test_register_function_exists(self) -> None:
        # Verificar se a função register existe e funciona
        from grpcAPI.server_plugins.loader import _get_plugin
        from grpcAPI.server_plugins.plugins.reflection import register

        # Limpar registry antes do teste
        _get_plugin.clear()

        # Chamar register
        register()

        # Verificar se foi registrado
        assert "reflection" in _get_plugin

        # Verificar se pode criar uma instância
        creator = _get_plugin["reflection"]
        instance = creator()
        assert isinstance(instance, ReflectionPlugin)
        assert instance.plugin_name == "reflection"

    @patch("grpc_reflection.v1alpha.reflection.enable_server_reflection")
    def test_on_add_service_no_duplicates(
        self,
        mock_enable_reflection,
        plugin: ReflectionPlugin,
        mock_server_wrapper: Mock,
    ) -> None:
        """Testar se não adiciona serviços duplicados no conjunto."""
        # Adicionar o mesmo serviço duas vezes
        plugin.on_add_service("TestService", mock_server_wrapper)
        plugin.on_add_service("TestService", mock_server_wrapper)

        # Deve ter chamado reflection duas vezes (comportamento normal)
        assert mock_enable_reflection.call_count == 2
        # Mas só ter um serviço no set (sem duplicatas)
        assert len(plugin._services) == 1
        assert "TestService" in plugin._services

    @patch("grpc_reflection.v1alpha.reflection.enable_server_reflection")
    def test_state_reflects_current_services(
        self,
        mock_enable_reflection,
        plugin: ReflectionPlugin,
        mock_server_wrapper: Mock,
    ) -> None:
        """Testar se o state reflete corretamente os serviços atuais."""
        initial_state = plugin.state
        assert len(initial_state["services"]) == 0

        plugin.on_add_service("ServiceA", mock_server_wrapper)
        state_after_one = plugin.state
        assert len(state_after_one["services"]) == 1
        assert "ServiceA" in state_after_one["services"]

        plugin.on_add_service("ServiceB", mock_server_wrapper)
        final_state = plugin.state
        assert len(final_state["services"]) == 2
        assert "ServiceA" in final_state["services"]
        assert "ServiceB" in final_state["services"]
