from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    Union,
)


class Visitor(Protocol):
    def visit_message(self, message: "MessageBlock") -> None: ...
    def visit_service(self, service: "ServiceBlock") -> None: ...
    def visit_oneof(self, oneof: "OneOfBlock") -> None: ...
    def visit_enum_block(self, enumblock: "EnumBlock") -> None: ...

    def visit_field(self, field: "Field") -> None: ...
    def visit_oneof_field(self, field: "OneOfField") -> None: ...
    def visit_method(self, method: "Method") -> None: ...
    def visit_enum_field(self, enumfield: "EnumField") -> None: ...


@dataclass
class Node:
    def accept(self, visitor: Visitor) -> None:
        raise NotImplementedError()


@dataclass
class Meta:

    block: Optional["Block"]

    description: str = ""
    options: Dict[str, Union[str, bool]] = field(
        default_factory=dict[str, Union[str, bool]]
    )

    render_dict: Dict[str, Union[str, bool]] = field(
        default_factory=dict[str, Union[str, bool]]
    )


@dataclass
class BaseField(Node):
    ftype: Optional[type[Any]]
    name: str
    number: Optional[int]


@dataclass
class Field(Meta, BaseField):

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_field(self)


@dataclass
class OneOfField(Meta, BaseField):

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_oneof_field(self)


@dataclass
class BaseEnumField(Node):
    name: str
    number: Optional[int]

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_enum_field(self)


@dataclass
class EnumField(Meta, BaseEnumField):
    pass


@dataclass
class BaseMethod(Node):
    name: str
    request_type: List[type[Any]]
    response_type: type[Any]

    method_func: Callable[..., Any]

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_method(self)


@dataclass
class Method(Meta, BaseMethod):
    pass


@dataclass
class BaseBlock(Node):
    protofile: str
    package: Union[str, object]

    name: str
    block_type: Literal["message", "enum", "oneof", "service"]
    fields: List[Union[Field, Method, "Block"]]

    def __len__(self) -> int:
        return len(self.fields)

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_block(self)

    @property
    def number(self) -> int:
        if self.block_type == "oneof":
            return min([f.number for f in self.fields])
        return 0


@dataclass
class Block(Meta, BaseBlock):
    reserveds: List[Union[int, range, str]] = field(
        default_factory=list[Union[int, range, str]]
    )

    @property
    def raw_reserved_indexes(self) -> List[Union[range, int]]:
        return [index for index in self.reserveds if not isinstance(index, str)]

    @property
    def reserved_indexes(self) -> List[int]:
        indexes = self.raw_reserved_indexes
        start = 0 if self.block_type == "enum" else 1
        flat = {
            i
            for x in indexes
            for i in (range(x.start, x.stop + 1) if isinstance(x, range) else [x])
            if i >= start
        }
        return list(flat)

    @property
    def reserved_keys(self) -> List[str]:
        return [key for key in self.reserveds if isinstance(key, str)]


T = TypeVar("T")


@dataclass
class BaseBlock2(Node, Generic[T]):
    protofile: str
    package: Union[str, object]

    name: str
    fields: List[T]
    start: int

    @property
    def number(self) -> int:
        return 0

    reserveds: List[Union[int, range, str]] = field(
        default_factory=list[Union[int, range, str]]
    )

    @property
    def raw_reserved_indexes(self) -> List[Union[range, int]]:
        return [index for index in self.reserveds if not isinstance(index, str)]

    @property
    def reserved_indexes(self) -> List[int]:
        indexes = self.raw_reserved_indexes
        flat = {
            i
            for x in indexes
            for i in (range(x.start, x.stop + 1) if isinstance(x, range) else [x])
            if i >= self.start
        }
        return list(flat)

    @property
    def reserved_keys(self) -> List[str]:
        return [key for key in self.reserveds if isinstance(key, str)]


class MessageBlock(BaseBlock2[Field], Meta):
    start: int = 1

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_message(self)


class ServiceBlock(BaseBlock2[Method], Meta):
    start: int = -1

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_service(self)


class OneOfBlock(MessageBlock):

    @property
    def number(self) -> int:
        return min((f.number for f in self.fields if f.number is not None), default=0)

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_oneof(self)


class EnumBlock(BaseBlock2[EnumField], Meta):
    start: int = -536870911

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_enum_field(self)


GenericItem = Union[Field, OneOfField, EnumField, Method]
GenericBlock = Union[MessageBlock, OneOfBlock, ServiceBlock, EnumBlock]


@dataclass
class ProtoBlocks:
    protofile: List[str]
    package: Union[str, object]

    version: int = 3
    imports: List[str] = field(default_factory=list[str])

    blocks: List[Block] = field(default_factory=list[Block])

    description: str = ""
    options: Dict[str, Union[str, bool]] = field(
        default_factory=dict[str, Union[str, bool]]
    )
