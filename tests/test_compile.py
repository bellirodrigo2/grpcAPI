import os
import shutil
import unittest
from pathlib import Path
from typing import Annotated, List

from grpcAPI.app import App, Package
from grpcAPI.makeproto.main import make_protos
from grpcAPI.makeproto.protoc_compiler import compile
from grpcAPI.types.base import Metadata, OneOf
from grpcAPI.types.types import Int32, String

app = App("test")

pack1 = Package("pack1")
pack2 = Package("pack2")

mod1 = pack1.Module("mod1", description="Module1")
mod2 = pack2.Module("mod2", description="Module2")


class TestApp(unittest.TestCase):
    def setUp(self) -> None:

        class UserCode(mod1.ProtoEnum):
            NOTFOUND = -247
            ACTIVE = 0
            INACTIVE = 1

        class UserInput(mod1.ProtoModel):
            name: Annotated[
                str,
                Metadata(
                    description="user name", options={"deprecated": True}, index=4
                ),
            ]
            code: UserCode = Metadata(options={"json_name": "user_code"})
            age: int = Metadata(description="user´s age")

        id_desc = "this is a long description that should be formatted, because it has more than 80 characteres"

        class User(UserInput):
            id: str = Metadata(description=id_desc)

        class UserNames(mod1.ProtoModel):
            names: List[String]
            student: str = OneOf(key="occupation", description="The school´s name")
            employee: str = OneOf(
                key="occupation", description="The employer´s name", index=1
            )

        class UserList(mod1.ProtoModel):
            users: List[User]
            index: Annotated[Int32, Metadata(index=12)]

        user_service = mod2.Service("user_service", description="User Services")

        @user_service(description="Make New User")
        def newuser(input: UserInput) -> User: ...

        @user_service(description="get a list of users")
        def getusers(input: UserNames) -> UserList: ...

        app.add_package(pack1)
        app.add_package(pack2)

        self.app = app
        self.output_dir = Path("./tests/test_compile_proto")
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            # pass

    def test_compile_proto(self) -> None:
        protos = make_protos(self.app.packages, {}, [])
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


if __name__ == "__main__":
    unittest.main()
