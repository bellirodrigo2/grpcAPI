from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Union


class Visitor(Protocol):
    def visit_block(self, block: "Block") -> None: ...

    # def visit_service(self, service: "ServiceBlock") -> None: ...
    # def visit_oneof(self, oneof: "OneOfBlock") -> None: ...
    # def visit_enum_block(self, enumblock: "EnumBlock") -> None: ...

    def visit_field(self, field: "Field") -> None: ...

    # def visit_oneof_field(self, field: "OneOfField") -> None: ...
    def visit_method(self, method: "Method") -> None: ...

    # def visit_enum_field(self, enumfield: "EnumField") -> None: ...


@dataclass
class Node:
    name: str
    number: Optional[int]

    block: Optional["Block"]
    render_dict: Dict[str, Union[str, bool]]

    @property
    def index(self) -> Optional[int]:
        return self.number

    @property
    def top_block(self) -> Optional["Block"]:
        return self.block

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
    @property
    def top_block(self) -> Optional["Block"]:
        if self.block is None:
            raise ValueError("OneOfField block cannot be None")
        return self.block.block


@dataclass
class Method(Node):
    request_type: List[type[Any]]
    response_type: type[Any]

    method_func: Callable[..., Any]

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_method(self)


@dataclass
class Block(Node):
    protofile: str
    package: Union[str, object]
    fields: List[Node]

    def __len__(self) -> int:
        return len(self.fields)

    def accept(self, visitor: Visitor) -> None:
        visitor.visit_block(self)

    @property
    def index(self) -> Optional[int]:
        return 0

    reserveds: List[Union[int, range, str]]
    counter: int

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
    pass


@dataclass
class EnumBlock(Block):
    pass


@dataclass
class OneOfBlock(Block):
    pass


@dataclass
class Service(Block):
    pass


def is_enum(item: Union[Block, Field]) -> bool:
    return isinstance(item, EnumBlock) or isinstance(item, EnumField)


min_enum = -536870911
