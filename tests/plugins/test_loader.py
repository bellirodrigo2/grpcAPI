import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from grpcAPI.server_plugins.loader import (
    _get_plugin,
    load_plugins,
    make_plugin,
    register,
    unregister,
)
from tests.plugins.helper import MockPlugin


class TestLoader:

    def setup_method(self) -> None:
        # Clear the plugin registry before each test
        _get_plugin.clear()

    def test_register_and_unregister(self) -> None:
        def mock_creator() -> MockPlugin:
            return MockPlugin("test")

        register("test_plugin", mock_creator)
        assert "test_plugin" in _get_plugin
        assert _get_plugin["test_plugin"] == mock_creator

        unregister("test_plugin")
        assert "test_plugin" not in _get_plugin

    def test_unregister_nonexistent(self) -> None:
        # Should not raise error
        unregister("nonexistent_plugin")

    def test_get_plugin_existing(self) -> None:
        def mock_creator() -> MockPlugin:
            return MockPlugin("test")

        register("test_plugin", mock_creator)
        plugin = make_plugin("test_plugin")

        assert isinstance(plugin, MockPlugin)
        assert plugin.plugin_name == "test"

    def test_get_plugin_with_loading(self) -> None:
        with patch("grpcAPI.server_plugins.loader.load_plugins") as mock_load:

            def mock_creator() -> MockPlugin:
                return MockPlugin("loaded")

            # Simulate plugin being loaded
            def side_effect(plugins):
                register(plugins[0], mock_creator)

            mock_load.side_effect = side_effect

            plugin = make_plugin("new_plugin")

            mock_load.assert_called_once_with(["new_plugin"])
            assert isinstance(plugin, MockPlugin)
            assert plugin.plugin_name == "loaded"

    def test_get_plugin_load_failure(self) -> None:
        with patch("grpcAPI.server_plugins.loader.load_plugins") as mock_load:
            mock_load.side_effect = FileNotFoundError("Plugin not found")

            with pytest.raises(ValueError, match="Plugin not found"):
                make_plugin("missing_plugin")

    def test_load_plugins_success(self) -> None:
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            plugins_dir = Path(temp_dir) / "plugins"
            plugins_dir.mkdir()

            # Create a mock plugin file
            plugin_file = plugins_dir / "test_plugin.py"
            plugin_content = """
def register():
    from grpcAPI.server_plugins.loader import register as reg
    def create_plugin():
        return type('TestPlugin', (), {'plugin_name': 'test'})()
    reg('test_plugin', create_plugin)
"""
            plugin_file.write_text(plugin_content)

            # Patch the base path
            with patch("grpcAPI.server_plugins.loader.Path") as mock_path:
                mock_path(__file__).parent = Path(temp_dir)
                mock_path.return_value.resolve.return_value = plugins_dir

                # This should work without raising exceptions
                load_plugins(["test_plugin"])

                # Verify plugin was registered
                assert "test_plugin" in _get_plugin

    def test_load_plugins_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plugins_dir = Path(temp_dir) / "plugins"
            plugins_dir.mkdir()

            with patch("grpcAPI.server_plugins.loader.Path") as mock_path:
                mock_path(__file__).parent = Path(temp_dir)
                mock_path.return_value.resolve.return_value = plugins_dir

                with pytest.raises(FileNotFoundError):
                    load_plugins(["nonexistent_plugin"])

    def test_load_plugins_no_register_function(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plugins_dir = Path(temp_dir) / "plugins"
            plugins_dir.mkdir()

            # Create plugin file without register function
            plugin_file = plugins_dir / "bad_plugin.py"
            plugin_file.write_text("# No register function")

            with patch("grpcAPI.server_plugins.loader.Path") as mock_path:
                mock_path(__file__).parent = Path(temp_dir)
                mock_path.return_value.resolve.return_value = plugins_dir

                with pytest.raises(
                    AttributeError, match="missing required 'register' function"
                ):
                    load_plugins(["bad_plugin"])
