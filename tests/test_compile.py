import os
import shutil
import unittest
from pathlib import Path

from grpcAPI.app import Package
from grpcAPI.makeproto.main import make_protos
from grpcAPI.makeproto.protoc_compiler import compile
from tests.test_app_helper import make_app

app = make_app()


class TestCompileApp(unittest.TestCase):
    def setUp(self) -> None:

        self.app = app
        self.output_dir = Path("./tests/test_compile_proto")
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            # pass

    def test_compile_proto(self) -> None:
        protos = make_protos(self.app.packages, {})
        if protos is None:
            raise
        for package, module_dict in protos.items():
            outdir = self.output_dir / package
            outdir.mkdir(exist_ok=True)
            for modulename, proto_str in module_dict.items():
                filename = f"{modulename}.proto"
                proto_path = outdir / filename
                with open(proto_path, "w", encoding="utf-8") as f:
                    f.write(proto_str)
                    f.flush()
                    os.fsync(f.fileno())
                result = compile(
                    tgt_folder=str(self.output_dir),
                    protofile=f"{package}/{filename}",
                    output_dir=str(self.output_dir),
                )
                self.assertTrue(result, "Falha na compilação")

    def test_invalid_package_name(self) -> None:
        with self.assertRaises(ValueError):
            Package("pack$1")


if __name__ == "__main__":
    unittest.main()
