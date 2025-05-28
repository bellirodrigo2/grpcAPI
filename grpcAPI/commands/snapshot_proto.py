import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from grpcAPI.schema import ISchema


def remove_proto_comments(proto_str: str) -> str:
    proto_str = re.sub(r"/\*.*?\*/", "", proto_str, flags=re.DOTALL)
    proto_str = re.sub(r"//.*$", "", proto_str, flags=re.MULTILINE)
    proto_str = re.sub(r"^[ \t]*\n", "", proto_str, flags=re.MULTILINE)

    return proto_str


@dataclass
class SerializableProto(ISchema[Dict[str, str]]):
    module: str
    package: str
    protofile: str

    def serialize(self) -> Dict[str, str]:
        return {
            "package": self.package,
            "module": self.module,
            "protofile": remove_proto_comments(self.protofile),
        }

    def hash(self) -> str:
        serialized = self.serialize()
        raw = json.dumps(serialized, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class SerializableApp(ISchema[Dict[str, Any]]):
    version: str
    appname: str
    modules: List[SerializableProto]

    def serialize(self) -> Dict[str, Any]:
        return {
            "appname": self.appname,
            "version": self.version,
            "modules": [mod.serialize() for mod in self.modules],
        }

    def hash(self) -> str:
        serialized = self.serialize()
        raw = json.dumps(serialized, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()
