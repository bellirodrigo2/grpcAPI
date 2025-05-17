
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, Protocol, Union


class Visitor(Protocol):
    def visit_block(self, block: "Block") -> None: ...
    def visit_field(self, field: "Field") -> None: ...
    def visit_method(self, method: "Method") -> None: ...


@dataclass
class Node:
    def accept(self, visitor: Visitor) -> None:
        raise NotImplementedError()

@dataclass
class Meta:

    block: "Block"

    description: str = ""
    options: Dict[str, Union[str, bool]] = field(
        default_factory=dict[str, Union[str, bool]]
    )

    def to_dict(self) -> Dict[str, Any]:
        _dict = asdict(self)
        del _dict["block"]
        return asdict(self)
    
@dataclass
class BaseField(Node):
    ftype: Optional[type[Any]]
    name: str
    number: int

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_field(self)

@dataclass
class Field(Meta,BaseField):
    pass

@dataclass
class BaseMethod(Node):
    name: str
    request_type: type[Any]
    response_type: type[Any]
    request_stream: bool
    response_stream: bool

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_method(self)

@dataclass
class Method(Meta,BaseMethod):
    pass

@dataclass
class BaseBlock(Node):
    protofile: str
    package: Union[str, object]

    name: str
    block_type: Literal["message", "enum", "oneof", "service"]
    fields: List[Union[Field, Method, "Block"]]

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_block(self)

    @property
    def number(self) -> int:
        if self.block_type == "oneof":
            return min([f.number for f in self.fields])
        return 0

@dataclass
class Block(Meta,BaseBlock):
    reserveds: List[Union[int, range,str]] = field(
        default_factory=list[Union[int, range,str]]
    )

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