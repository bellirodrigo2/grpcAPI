import tempfile
from pathlib import Path

from grpcAPI.commands.init import InitCommand, run_init


class TestInitCommand:
    """Test cases for InitCommand."""

    def test_init_command_creates_config_file(self):
        """Test that init command creates config file in specified directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            init_cmd = InitCommand()
            init_cmd.run_sync(dst=tmp_path)

            config_file = tmp_path / "grpcapi.config.json"
            assert config_file.exists()

            # Verify content is copied from source
            content = config_file.read_text(encoding="utf-8")
            assert "proto_path" in content
            assert "lib_path" in content

    def test_init_command_warns_if_file_exists(self):
        """Test that init command warns when config file already exists."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            config_file = tmp_path / "grpcapi.config.json"
            config_file.write_text("{}", encoding="utf-8")

            init_cmd = InitCommand()
            init_cmd.run_sync(dst=tmp_path)

            # File should not be overwritten without force flag
            assert config_file.read_text(encoding="utf-8") == "{}"

    def test_init_command_overwrites_with_force(self):
        """Test that init command overwrites existing file with force flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            config_file = tmp_path / "grpcapi.config.json"
            config_file.write_text("{}", encoding="utf-8")

            init_cmd = InitCommand()
            init_cmd.run_sync(dst=tmp_path, force=True)

            # File should be overwritten
            content = config_file.read_text(encoding="utf-8")
            assert "proto_path" in content
            assert content != "{}"

    def test_run_init_standalone_function(self):
        """Test the standalone run_init function."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            run_init(dst=tmp_path)

            config_file = tmp_path / "grpcapi.config.json"
            assert config_file.exists()

            content = config_file.read_text(encoding="utf-8")
            assert "proto_path" in content

    def test_run_init_with_force(self):
        """Test run_init function with force parameter."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            config_file = tmp_path / "grpcapi.config.json"
            config_file.write_text("{}", encoding="utf-8")

            run_init(force=True, dst=tmp_path)

            content = config_file.read_text(encoding="utf-8")
            assert "proto_path" in content
            assert content != "{}"
