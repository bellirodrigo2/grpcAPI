import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from grpcAPI.app import APIService, App, GrpcAPI
from grpcAPI.commands.build import BuildCommand, build_protos
from grpcAPI.makeproto.interface import IProtoPackage
from grpcAPI.singleton import SingletonMeta


@pytest.fixture(autouse=True)
def reset_singleton():
    """Clear GrpcAPI singleton state before each test"""
    SingletonMeta._instances.clear()
    yield
    SingletonMeta._instances.clear()


class TestBuildProtos:
    """Test the build_protos function directly"""

    def test_build_protos_normal_mode(self, functional_service: APIService) -> None:
        """Test build_protos without zip compression"""
        app = App()
        app.add_service(functional_service)
        logger = Mock()

        mock_proto = Mock(spec=IProtoPackage)
        mock_proto.package = "test_package"
        mock_proto.filename = "test_service"
        mock_proto.content = 'syntax = "proto3";\nservice TestService {}'
        mock_proto.depends = set()
        mock_proto.qual_name = "test_service.proto"

        with tempfile.TemporaryDirectory() as temp_dir:
            proto_path = Path(temp_dir) / "proto"
            output_path = Path(temp_dir) / "output"
            proto_path.mkdir()
            output_path.mkdir()

            with patch("grpcAPI.commands.build.lint.run_lint") as mock_lint, patch(
                "grpcAPI.commands.build.write_protos"
            ) as mock_write, patch(
                "grpcAPI.commands.build.copy_proto_files"
            ) as mock_copy:

                mock_lint.return_value = [mock_proto]
                mock_write.return_value = {"test_service.proto"}

                result = build_protos(
                    app,
                    logger,
                    proto_path,
                    output_path,
                    overwrite=True,
                    clean_services=True,
                    zipcompress=False,
                )

                mock_lint.assert_called_once_with(app, logger)
                mock_write.assert_called_once_with(
                    proto_stream=[mock_proto],
                    out_dir=output_path,
                    overwrite=True,
                    clean_services=True,
                )
                mock_copy.assert_called_once_with(proto_path, output_path, logger)
                assert result == {"test_service.proto"}

    def test_build_protos_zip_mode(self, functional_service: APIService) -> None:
        """Test build_protos with zip compression"""
        app = App()
        app.add_service(functional_service)
        logger = Mock()

        mock_proto = Mock(spec=IProtoPackage)
        mock_proto.package = "test_package"
        mock_proto.filename = "test_service"
        mock_proto.content = 'syntax = "proto3";\nservice TestService {}'
        mock_proto.depends = set()
        mock_proto.qual_name = "test.proto"

        with tempfile.TemporaryDirectory() as temp_dir:
            proto_path = Path(temp_dir) / "proto"
            output_path = Path(temp_dir) / "output"
            proto_path.mkdir()
            output_path.mkdir()

            with patch("grpcAPI.commands.build.lint.run_lint") as mock_lint, patch(
                "grpcAPI.commands.build.write_protos"
            ) as mock_write, patch(
                "grpcAPI.commands.build.copy_proto_files"
            ) as mock_copy, patch(
                "grpcAPI.commands.build.zip_directory"
            ) as mock_zip:

                mock_lint.return_value = [mock_proto]
                mock_write.return_value = {"test.proto"}

                result = build_protos(
                    app,
                    logger,
                    proto_path,
                    output_path,
                    overwrite=True,
                    clean_services=True,
                    zipcompress=True,
                )

                mock_lint.assert_called_once_with(app, logger)
                assert mock_write.call_count == 1
                assert mock_copy.call_count == 1
                mock_zip.assert_called_once()
                assert result == {"test.proto"}


class TestBuildCommand:
    """Test the BuildCommand class"""

    def test_build_command_init(self):
        """Test BuildCommand initialization"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ) as mock_run_process:

            def setup_singleton(app_path: str):
                GrpcAPI()

            mock_load_app.side_effect = setup_singleton

            cmd = BuildCommand("test_app:app", None)

            assert cmd.command_name == "build"
            assert cmd.app_path == "test_app:app"
            assert isinstance(cmd.app, GrpcAPI)

            mock_load_app.assert_called_once_with("test_app:app")
            mock_run_process.assert_called_once()

    async def test_build_command_run(self, functional_service):
        """Test BuildCommand.run() method"""
        with patch("grpcAPI.commands.command.load_app") as mock_load_app, patch(
            "grpcAPI.commands.command.run_process_service"
        ):

            def setup_singleton(app_path: str):
                app = GrpcAPI()
                app.add_service(functional_service)

            mock_load_app.side_effect = setup_singleton

            cmd = BuildCommand("test_app:app", None)

            with patch("grpcAPI.commands.build.build_protos") as mock_build:
                mock_build.return_value = {"test.proto"}

                with patch(
                    "grpcAPI.commands.utils.get_proto_lib_path"
                ) as mock_paths, patch(
                    "grpcAPI.commands.utils.get_compile_proto_settings"
                ) as mock_settings:

                    mock_paths.return_value = (Path("proto"), Path("lib"))
                    mock_settings.return_value = (True, False)

                    await cmd.run(zipcompress=True)

                    mock_build.assert_called_once_with(
                        app=cmd.app,
                        logger=cmd.logger,
                        proto_path=Path("proto"),
                        output_path=Path("lib"),
                        overwrite=False,
                        clean_services=True,
                        zipcompress=True,
                    )

    def test_singleton_behavior_across_commands(self, functional_service):
        """Test that multiple BuildCommand instances share the same GrpcAPI singleton"""
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

            cmd1 = BuildCommand("test_app:app", None)
            cmd2 = BuildCommand("another_app:app", None)

            assert cmd1.app is cmd2.app
