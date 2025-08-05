from unittest.mock import Mock, patch

import pytest

from grpcAPI.server_plugins.plugins.health_check import HealthCheckPlugin


class TestHealthCheckPlugin:

    @pytest.fixture
    def plugin(self) -> HealthCheckPlugin:
        return HealthCheckPlugin(grace=1.0)

    @pytest.fixture
    def mock_server_wrapper(self) -> Mock:
        wrapper = Mock()
        wrapper.server = Mock()
        return wrapper

    def test_init(self) -> None:
        plugin = HealthCheckPlugin(grace=2.0)
        assert plugin.plugin_name == "health_check"
        assert plugin.grace == 2.0
        assert len(plugin._services_set) == 0

    def test_state_property(self, plugin: HealthCheckPlugin) -> None:
        plugin._services_set.add("TestService")
        state = plugin.state

        assert state["name"] == "health_check"
        assert "TestService" in state["services"]
        assert state["grace"] == 1.0

    @patch(
        "grpcAPI.server_plugins.plugins.health_check.health_pb2_grpc.add_HealthServicer_to_server"
    )
    def test_on_register(
        self, mock_add_servicer, plugin: HealthCheckPlugin, mock_server_wrapper: Mock
    ) -> None:
        plugin.on_register(mock_server_wrapper)

        mock_add_servicer.assert_called_once_with(
            plugin._servicer, mock_server_wrapper.server
        )
        assert "" in plugin._services_set

    def test_on_add_service(self, plugin) -> None:
        mock_server = Mock()
        plugin.on_add_service("TestService", mock_server)

        assert "TestService" in plugin._services_set

    @pytest.mark.asyncio
    async def test_on_stop_with_grace(self, plugin: HealthCheckPlugin) -> None:
        plugin._services_set.add("TestService")
        plugin._services_set.add("")

        with patch("asyncio.sleep") as mock_sleep:
            await plugin.on_stop()
            mock_sleep.assert_called_once_with(1.0)

    @pytest.mark.asyncio
    async def test_on_stop_without_grace(self) -> None:
        plugin = HealthCheckPlugin(grace=None)
        plugin._services_set.add("TestService")

        with patch("asyncio.sleep") as mock_sleep:
            await plugin.on_stop()
            mock_sleep.assert_not_called()
