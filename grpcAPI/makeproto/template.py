import logging
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from typing_extensions import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Protocol,
    Set,
)

from grpcAPI.makeproto.interface import IMetaType

logger = logging.getLogger(__name__)


class Visitor(Protocol):
    def visit_service(self, block: "ServiceTemplate") -> None: ...  # pragma: no cover
    def visit_method(self, method: "MethodTemplate") -> None: ...  # pragma: no cover


class ToDict(Protocol):
    def to_dict(self) -> Dict[str, Any]: ...  # pragma: no cover


@dataclass
class Node:
    name: str
    comments: str
    options: Iterable[str]

    def accept(self, visitor: Visitor) -> None:
        raise NotImplementedError()  # pragma: no cover


@dataclass
class MethodTemplate(Node, ToDict):
    service: "ServiceTemplate"

    method_func: Callable[..., Any]
    name: str
    request_types: List[IMetaType]
    response_type: Optional[IMetaType]
    request_stream: bool = False
    response_stream: bool = False

    request_str: Optional[str] = None
    response_str: Optional[str] = None

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_method(self)

    def to_dict(self) -> Dict[str, Any]:
        self_dict: Dict[str, Any] = {}

        self_dict["name"] = self.name
        self_dict["comment"] = self.comments

        self_dict["options"] = self.options

        self_dict["request_type"] = self.request_str
        self_dict["response_type"] = self.response_str

        self_dict["request_stream"] = self.request_stream
        self_dict["response_stream"] = self.response_stream

        return self_dict


@dataclass
class ServiceTemplate(Node, ToDict):
    package: str
    module: str
    methods: List[MethodTemplate]

    def __hash__(self) -> int:
        return hash((self.package, self.module, self.name))

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_service(self)

    def __eq__(self, other: object) -> bool:
        try:
            return (
                self.package == other.package  # type: ignore
                # and self.module == other.module  # type: ignore
                and self.name == other.name  # type: ignore
            )
        except AttributeError:  # pragma: no cover
            return False

    def to_dict(self) -> Dict[str, Any]:
        self_dict: Dict[str, Any] = {}
        if not self.methods:
            logger.warning(
                f"Service: '{self.package}.{self.name}' is empty and it was ignored"
            )
            return self_dict

        self_dict["service_name"] = self.name
        self_dict["service_comment"] = self.comments
        self_dict["options"] = self.options

        methods_dict: List[Dict[str, Any]] = []
        for method in self.methods:
            method_dict = method.to_dict()
            methods_dict.append(method_dict)
        self_dict["methods"] = methods_dict

        return self_dict


@dataclass
class ProtoTemplate(ToDict):
    comments: str
    syntax: int
    package: str
    module: str
    imports: Set[str]
    services: List[ServiceTemplate]
    options: List[str]

    def to_dict(self) -> Dict[str, Any]:
        self_dict: Dict[str, Any] = {}
        if not self.services:
            logger.warning(
                f"Protofile: '{self.package or 'NO_PACKAGE'}.{self.module}.proto' is empty and it was ignored"
            )
            return self_dict

        self_dict["comment"] = self.comments
        self_dict["syntax"] = f"proto{self.syntax}"
        self_dict["package"] = self.package
        self_dict["imports"] = self.imports
        self_dict["options"] = self.options

        services_dict: List[Dict[str, Any]] = []
        for service in self.services:
            service_dict = service.to_dict()
            if not service_dict:
                continue
            services_dict.append(service_dict)
        self_dict["services"] = services_dict

        return self_dict


TEMPLATE_DIR = Path(__file__).parent / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR), trim_blocks=True, lstrip_blocks=True
)


def render_service_template(data: Dict[str, str]) -> str:
    template = env.get_template("service.j2")
    return template.render(data)


def render_protofile_template(data: Dict[str, str]) -> str:
    if not data:
        return ""
    env.globals["render_service_template"] = render_service_template
    template = env.get_template("protofile.j2")
    return template.render(data)
