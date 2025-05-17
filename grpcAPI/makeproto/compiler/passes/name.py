import re
from enum import Enum, auto
from typing import Callable, Dict, Set, Union

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass

VALID_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


PROTOBUF_RESERVED_WORDS = {
    "syntax",
    "import",
    "option",
    "package",
    "message",
    "enum",
    "service",
    "rpc",
    "returns",
    "reserved",
    "repeated",
    "optional",
    "required",
    "map",
    "oneof",
    "extensions",
    "extend",
    "group",
    "true",
    "false",
}


class NameValidator(CompilerPass):
    def _visit(self, item: Union[Block, Field, Method], name: str) -> None:

        if isinstance(item, Field):
            what = "field"
            block_name = item.block.name
        elif isinstance(item, Method):
            what = "method"
            block_name = item.block.name
        else:
            what = "block"
            block_name = item.name

        report = self.ctx.get_report(block_name)

        if not VALID_NAME_RE.match(name):
            report.add_error(name, f"Invalid {what} name: '{name}'", code="E101")
        if name in PROTOBUF_RESERVED_WORDS:
            report.add_error(
                name, f"Protobuf reserved {what} name: '{name}'", code="E102"
            )

    def visit_block(self, block: Block) -> None:
        block_name = block.name
        self._visit(block, block_name)

        report = self.ctx.get_report(block.name)

        used_names: Set[str] = set()

        for field in block.fields:
            name = field.name
            if name in block.reserveds:
                report.add_error(
                    name,
                    f"Name '{name}' is reserved in block '{block.name}'",
                    code="E103",
                )
            elif name in used_names:
                report.add_error(
                    name,
                    f"Duplicated name '{name}' in the block '{block.name}'",
                    code="E104",
                )
            else:
                used_names.add(name)
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        name = field.name
        self._visit(field, name)

    def visit_method(self, method: Method) -> None:
        name = method.name
        self._visit(method, name)


# -------------- Name Transform ----------------


class NameTransformStrategy(Enum):
    NO_TRANSFORM = auto()
    SNAKE_CASE = auto()
    CAMEL_CASE = auto()
    PASCAL_CASE = auto()


def to_snake_case(name: str) -> str:
    name = re.sub(r"[\-\s]+", "_", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"__+", "_", name)
    return name.lower()


def to_camel_case(name: str) -> str:
    parts = re.split(r"[_\-\s]+", name)
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])


def to_pascal_case(name: str) -> str:
    parts = re.split(r"[_\-\s]+", name)
    return "".join(word.capitalize() for word in parts)


name_strategy: Dict[NameTransformStrategy, Callable[[str], str]] = {
    NameTransformStrategy.SNAKE_CASE: to_snake_case,
    NameTransformStrategy.CAMEL_CASE: to_camel_case,
    NameTransformStrategy.PASCAL_CASE: to_pascal_case,
}


def normalize_name(name: str, strategy: NameTransformStrategy) -> str:
    transform = name_strategy.get(strategy, lambda x: x)
    return transform(name)


class NameNormalizer(CompilerPass):
    def __init__(
        self, strategy: NameTransformStrategy = NameTransformStrategy.NO_TRANSFORM
    ):
        self.strategy = strategy

    def visit_block(self, block: Block) -> None:
        block.name = normalize_name(block.name, self.strategy)
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        field.name = normalize_name(field.name, self.strategy)

    def visit_method(self, method: Method) -> None:
        method.name = normalize_name(method.name, self.strategy)
