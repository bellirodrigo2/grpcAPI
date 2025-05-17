import re
from enum import Enum, auto
from typing import Callable, Dict, Set, Union

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode

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

# --------- Name Validation Pass ------------


class NameValidator(CompilerPass):
    def _visit(self, item: Union["Block", "Field", "Method"], name: str) -> None:
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
            report.report_error(
                code=CompileErrorCode.INVALID_NAME,
                location=name,
                override_msg=f"Invalid {what} name: '{name}'",
            )
        if name in PROTOBUF_RESERVED_WORDS:
            report.report_error(
                code=CompileErrorCode.RESERVED_NAME,
                location=name,
                override_msg=f"Protobuf reserved {what} name: '{name}'",
            )

    def visit_block(self, block: "Block") -> None:
        block_name = block.name
        self._visit(block, block_name)

        report = self.ctx.get_report(block.name)
        used_names: Set[str] = set()

        for field in block.fields:
            name = field.name
            if name in block.reserveds:
                report.report_error(
                    code=CompileErrorCode.NAME_RESERVED_IN_BLOCK,
                    location=name,
                    override_msg=f"Name '{name}' is reserved in block '{block.name}'",
                )
            elif name in used_names:
                report.report_error(
                    code=CompileErrorCode.DUPLICATED_NAME,
                    location=name,
                    override_msg=f"Duplicated name '{name}' in the block '{block.name}'",
                )
            else:
                used_names.add(name)
            field.accept(self)

    def visit_field(self, field: "Field") -> None:
        self._visit(field, field.name)

    def visit_method(self, method: "Method") -> None:
        self._visit(method, method.name)


# --------- Name Normalizer ------------------


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
    # quebra por underscore, hífen ou espaço
    parts = re.split(r"[_\-\s]+", name)
    if not parts:
        return ""
    # força só a primeira letra da primeira parte a minúscula
    first = parts[0]
    first = first[0].lower() + first[1:] if first else ""
    # capitaliza cada parte subsequente
    rest = "".join(word.capitalize() for word in parts[1:])
    return first + rest


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

    def visit_block(self, block: "Block") -> None:
        block.name = normalize_name(block.name, self.strategy)
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: "Field") -> None:
        field.name = normalize_name(field.name, self.strategy)

    def visit_method(self, method: "Method") -> None:
        method.name = normalize_name(method.name, self.strategy)
