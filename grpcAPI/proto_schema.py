import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, get_args

from typing_extensions import get_origin

from grpcAPI.persutil import (
    ISchema,
    WritePackage,
    create_snapshot,
    get_version_paths,
    write_atomic,
)
from grpcAPI.typemapping import map_model_fields
from grpcAPI.types import BaseEnum, BaseMessage, IModule, IPackage, OneOf


def type_to_str(tp: type[Any]) -> str:
    origin = get_origin(tp)
    args = get_args(tp)
    if origin is None:
        return tp.__name__ if hasattr(tp, "__name__") else str(tp)
    name = (
        origin.__name__
        if hasattr(origin, "__name__")
        else str(origin).split(".")[-1].split("'")[0]
    )
    args_str = ", ".join(type_to_str(arg) for arg in args)
    return f"{name}[{args_str}]"


@dataclass
class EnumSchema(ISchema[Dict[str, Any]]):
    cls: type[BaseEnum]

    def serialize(self) -> Dict[str, Any]:
        return {
            "module": self.cls.__module__,
            "qualname": self.cls.__qualname__,
            "package": str(self.cls.package()),
            "protofile": self.cls.protofile(),
            "fields": sorted((member.name, member.value) for member in self.cls),
        }

    def hash(self) -> str:
        serial = self.serialize()
        json_str = json.dumps(serial, sort_keys=True)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


@dataclass
class ClassSchema(ISchema[Dict[str, Any]]):
    cls: type[BaseMessage]

    def _get_fields(self) -> Set[Tuple[str, str, Optional[str]]]:

        self_set: Set[Tuple[str, str, Optional[str]]] = set()
        fields = map_model_fields(self.cls)
        for field in fields:
            oneofkey = field.getinstance(OneOf)
            key = oneofkey.key if oneofkey else None
            field_tuple: Tuple[str, str, Optional[str]] = (
                field.name,
                type_to_str(field.basetype),
                key,
            )
            self_set.add(field_tuple)
        return self_set

    def serialize(self) -> Dict[str, Any]:
        return {
            "module": self.cls.__module__,
            "qualname": self.cls.__qualname__,
            "package": str(self.cls.package()),
            "protofile": self.cls.protofile(),
            "fields": list(self._get_fields()),
        }

    def hash(self) -> str:
        serial = self.serialize()
        json_str = json.dumps(serial, sort_keys=True)  # ordena chaves para consistência
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


@dataclass
class MethodSchema(ISchema[Dict[str, Any]]):
    method: Callable[..., Any]
    type_based: Dict[str, type[Any]]  # one, type
    instance_based: Dict[str, Any]  # multiple, instance

    def _get_type(self, btype: type[Any]) -> Tuple[Optional[str], str]:
        # (field_name, qualified package name)
        return ("", "")

    def _get_instance(self, binst: type[Any]) -> Optional[str]:
        # field_name or None
        return None

    def serialize(self) -> Dict[str, Any]:

        # request = self._get_request()
        # context = self._get_context()
        # depends = self._get_depends()  # list
        # fromrequest = self._get_fromrequest()  # list
        # fromcontext = self._get_fromcontext()  # list
        # response = self._get_response()

        return {
            "name": self.method.__name__,
            "request": (False, {}),  # stream e classschema
            "context": None,  # field or None
            "depends": [],  # (name, type, signature)
            "fromcontext": [],  # (name, field)
            "fromrequest": [],  # (name, field)
            "response": (False, {}),  # stream e classschema
        }

    def hash(self) -> str:
        return ""


@dataclass
class ModuleSchema(ISchema[Dict[str, Any]]):
    module: IModule

    def serialize(self) -> Dict[str, Any]:
        return {}
        #     "version": self.module.version,
        #     "protofile": self.module.name,
        #     "package": self.module.package,
        #     "imports": sorted(self.module.imports),
        #     "options": dict(sorted(self.module.options.items())),
        #     "comment": self.module.description,
        #     "blocks": {
        #         block.name: {
        #             "name": block.name,
        #             "fields": sorted(
        #                 [
        #                     {"name": f.name, "type": f.ftype, "number": f.number}
        #                     for f in block.fields
        #                 ],
        #                 key=lambda x: x["number"],
        #             ),
        #             "comment": block.comment,
        #             "options": block.options,
        #             "reserved_indexes": sorted(block.reserved_index),
        #             "reserved_names": sorted(block.reserved_keys),
        #         }
        #         for block in sorted(self.proto.blocks, key=lambda b: b.name)
        #     },
        # }

    def hash(self) -> str:
        return ""
        # serialized = self.serialize()
        # raw = json.dumps(serialized, sort_keys=True)
        # return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class AppSchema(ISchema[Dict[str, Any]]):
    app: List[IPackage]

    def serialize(self) -> Dict[str, Any]:
        return {}

    def hash(self) -> str:
        return ""


def create_app_schema(packages: List[IPackage]) -> str:
    packs_schema = AppSchema(packages)
    schema = create_snapshot(packs_schema)
    return json.dumps(schema, indent=2, sort_keys=True)


def make_path_content_list(modules: Dict[str, Dict[str, str]]) -> List[Tuple[str, str]]:

    all_modules: Set[Tuple[str, str]] = set()

    for package, proto_dict in modules.items():
        for modulename, proto_text in proto_dict.items():
            proto_path = f"{package}/{modulename}.proto"
            all_modules.add((proto_text, proto_path))
    return list(all_modules)


def persist_protos(
    output_dir: Path,
    version_mode: str,
    protos_dict: Dict[str, Dict[str, str]],
    packs_list: List[IPackage],
) -> None:

    output_subdir, (schema_dir, schema_file) = get_version_paths(
        output_dir, version_mode
    )

    protos_file = make_path_content_list(protos_dict)
    protos_write_pack = WritePackage(
        parent_dir=output_subdir,
        clear_parent=True,
        contents=protos_file,
    )

    schema = create_app_schema(packs_list)
    schema_write_pack = WritePackage(
        parent_dir=schema_dir,
        clear_parent=False,
        contents=[(schema, schema_file)],
    )

    write_atomic(output_dir, [protos_write_pack, schema_write_pack])
