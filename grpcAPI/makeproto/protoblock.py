from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Type, Union


class Visitor(Protocol):
    def visit_block(self, block: "Block") -> None: ...
    def visit_field(self, field: "Field") -> None: ...
    def visit_method(self, method: "Method") -> None: ...


@dataclass
class Node:
    name: str
    number: Optional[int]

    description: str
    options: Dict[str, Union[bool, str]]

    block: Optional["Block"]
    render_dict: Dict[str, Any]

    @property
    def index(self) -> Optional[int]:
        return self.number

    @property
    def top_block(self) -> Optional["Block"]:
        return self.block

    def get_render_dict(self) -> Dict[str, Any]:
        return self.render_dict

    def accept(self, visitor: Visitor) -> None:
        raise NotImplementedError()


@dataclass
class Field(Node):
    ftype: Optional[type[Any]]

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_field(self)


@dataclass
class EnumField(Field):
    ftype: Optional[type[Any]] = None


@dataclass
class OneOfField(Field):
    key: str

    @property
    def top_block(self) -> Optional["Block"]:
        if self.block is None:
            raise ValueError("OneOfField block cannot be None")
        return self.block.block


@dataclass
class Method(Node):
    request_type: List[type[Any]]
    response_type: Type[Any]

    method_func: Callable[..., Any]

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_method(self)


@dataclass
class Block(Node):
    protofile: str
    package: Union[str, object]
    fields: List[Node]
    reserveds: List[Union[int, range, str]]
    counter: int = 1

    def __len__(self) -> int:
        return len(self.fields)

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_block(self)

    def get_render_dict(self) -> Dict[str, Any]:
        fields = []
        for field in self.fields:
            fields.append(field.get_render_dict())
        self.render_dict["fields"] = fields
        return super().get_render_dict()

    @property
    def index(self) -> Optional[int]:
        return 0

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
            if i >= self.counter
        }
        return list(flat)

    @property
    def reserved_keys(self) -> List[str]:
        return [key for key in self.reserveds if isinstance(key, str)]


@dataclass
class MessageBlock(Block):

    def __post_init__(self) -> None:
        self.render_dict["block_type"] = "message"


@dataclass
class EnumBlock(Block):

    def __post_init__(self) -> None:
        self.render_dict["block_type"] = "enum"


@dataclass
class OneOfBlock(Block):
    @property
    def index(self) -> Optional[int]:
        return min([f.index for f in self.fields if f.index is not None])

    def __post_init__(self) -> None:
        self.render_dict["block_type"] = "oneof"


@dataclass
class ServiceBlock(Block):

    def __post_init__(self) -> None:
        self.render_dict["block_type"] = "service"


def is_enum(item: Union[Block, Field]) -> bool:
    return isinstance(item, EnumBlock) or isinstance(item, EnumField)
