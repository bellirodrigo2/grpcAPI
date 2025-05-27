import os
import shutil
import unittest
from pathlib import Path
from typing import Any, Dict

from grpcAPI.makeproto.protoc_compiler import compile
from grpcAPI.makeproto.render.render import BaseModuleTemplate

message_block: Dict[str, Any] = {
    "block_type": "message",
    "name": "Person",
    "options": [],
    "reserveds": ['"name"', "12 to 16"],
    "fields": [
        {"name": "id", "ftype": "int32", "number": 1, "options": []},
        {
            "name": "email",
            "ftype": "string",
            "number": 2,
            "options": [],
        },
        {
            "block_type": "oneof",
            "name": "contact",
            "fields": [
                {"name": "phone", "ftype": "string", "number": 3, "options": []},
                {"name": "address", "ftype": "string", "number": 4, "options": []},
            ],
        },
    ],
}

enum_block: Dict[str, Any] = {
    "block_type": "enum",
    "name": "Status",
    "options": [],
    "reserveds": [],  # removido valores vazios
    "fields": [
        {"name": "ACTIVE", "ftype": None, "number": 0, "options": []},
        {"name": "INACTIVE", "ftype": None, "number": 1, "options": []},
    ],
}

service_block: Dict[str, Any] = {
    "block_type": "service",
    "name": "UserService",
    "options": [],  # removido deprecated (inválido para service)
    "reserveds": [],  # removido reserveds vazios
    "fields": [
        {
            "name": "GetPerson",
            "request_type": "Person",
            "request_stream": False,
            "response_type": "Person",
            "response_stream": False,
            "options": [],  # removido timeout (inválido no body do rpc)
        },
        {
            "name": "ListPersons",
            "request_type": "Person",
            "request_stream": True,
            "response_type": "Person",
            "response_stream": True,
            "options": [],
        },
    ],
}


class TestRender(unittest.TestCase):
    def setUp(self) -> None:
        self.proto_template = BaseModuleTemplate(
            modulename="proto1",
            package="pack1",
            version=3,
            description="//TesteFile",
            options={},
            # imports=["google/protobuf/timestamp.proto"],
            imports=[],
            fields=[],
        )
        self.output_dir = Path("./tests/test_render")
        self.output_dir.mkdir(exist_ok=True)
        self.proto_path = self.output_dir / "proto1.proto"

    def tearDown(self) -> None:
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        # pass

    def test_str(self) -> None:
        self.proto_template.add_field(enum_block)
        self.proto_template.add_field(message_block)
        self.proto_template.add_field(service_block)
        rendered = self.proto_template.render()

        with open(self.proto_path, "w", encoding="utf-8") as f:
            f.write(rendered)
            f.flush()
            os.fsync(f.fileno())

        result = compile(
            tgt_folder=str(self.output_dir),
            protofile=self.proto_path.name,
            output_dir=str(self.output_dir),
        )
        self.assertTrue(result, "Falha na compilação")
