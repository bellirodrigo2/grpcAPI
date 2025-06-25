import shutil
import unittest
from pathlib import Path

from grpcAPI.commands.compile import compile_proto
from grpcAPI.protoc_compiler import compile
from tests.test_app_helper import make_app

app = make_app()


class TestFullApp(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app
        self.output_dir_str = "./tests/test_compile_app"
        self.output_dir = Path(self.output_dir_str)
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            # pass

    def test_compile_proto_new(self) -> None:
        settings = {"output_dir": self.output_dir_str}
        self.assertFalse((self.output_dir / "V1").is_dir())
        compile_proto("grpcAPI/singleton.py", "new", settings)
        self.assertTrue((self.output_dir / "V1").is_dir())
        self.assertFalse((self.output_dir / "V2").is_dir())
        compile_proto("grpcAPI/singleton.py", "new", settings)
        self.assertTrue((self.output_dir / "V1").is_dir())
        self.assertTrue((self.output_dir / "V2").is_dir())

    def test_compile_proto_overwrite(self) -> None:
        settings = {"output_dir": self.output_dir_str}
        self.assertFalse((self.output_dir / "V1").is_dir())
        compile_proto("grpcAPI/singleton.py", "new", settings)
        self.assertTrue((self.output_dir / "V1").is_dir())
        self.assertFalse((self.output_dir / "V2").is_dir())
        compile_proto("grpcAPI/singleton.py", "overwrite", settings)
        self.assertTrue((self.output_dir / "V1").is_dir())
        self.assertFalse((self.output_dir / "V2").is_dir())

    def test_compile_proto_draft(self) -> None:
        settings = {"output_dir": self.output_dir_str}
        self.assertFalse((self.output_dir / "V1").is_dir())
        compile_proto("grpcAPI/singleton.py", "new", settings)
        self.assertTrue((self.output_dir / "V1").is_dir())
        self.assertFalse((self.output_dir / "draft").is_dir())
        compile_proto("grpcAPI/singleton.py", "draft", settings)
        self.assertTrue((self.output_dir / "V1").is_dir())
        self.assertTrue((self.output_dir / "draft").is_dir())

    def test_compile_proto(self) -> None:
        settings = {"output_dir": self.output_dir_str}
        compile_proto("grpcAPI/singleton.py", "new", settings)

        def list_files(path: Path) -> list[Path]:
            return [p for p in path.iterdir()]

        v1 = self.output_dir / "V1"
        for pack in list_files(v1):
            for proto in list_files(pack):
                result = compile(
                    tgt_folder=str(v1),
                    protofile=f"{str(proto.parent.name)}/{proto.name}",
                    output_dir=str(self.output_dir / "compiled"),
                )
                self.assertTrue(result)
