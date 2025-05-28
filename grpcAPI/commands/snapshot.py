from dataclasses import dataclass
from typing import Any, Dict, Union

from grpcAPI.schema import ISchema
from grpcAPI.types import BaseEnum, BaseMessage, IModule, IService
from grpcAPI.types.interfaces import IMethod

# class IModule(Protocol):
#     name: str
#     package: Union[_NoPackage, str]
#     description: str
#     options: ProtoOption

#     @property
#     def services(self) -> List[IService]: ...


#     @property
#     def objects(self) -> Set[type[Union[BaseMessage, BaseEnum]]]: ...
# class IMethod(Protocol):
#     method: Callable[..., Any]
#     description: str
#     options: ProtoOption


# class IService(Protocol):
#     name: str
#     module: str
#     package: Union[str, _NoPackage]
#     methods: List[IMethod]
#     description: str
#     options: ProtoOption


@dataclass
class MethodSchema(ISchema[Dict[str, Any]]):
    method: IMethod

    def serialize(self) -> Dict[str, Any]:
        return {}

    def hash(self) -> str:
        return ""


@dataclass
class ServiceSchema(ISchema[Dict[str, Any]]):
    service: IService

    def serialize(self) -> Dict[str, Any]:
        return {}

    def hash(self) -> str:
        return ""


@dataclass
class ClassSchema(ISchema[Dict[str, Any]]):
    cls: type[Union[BaseMessage, BaseEnum]]

    def serialize(self) -> Dict[str, Any]:
        return {}

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
