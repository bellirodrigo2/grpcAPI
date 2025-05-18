# --------- Name Normalizer ------------------


import re
from enum import Enum, auto
from typing import Callable, Dict, Optional

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass


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


DEFAULT_CASE = NameTransformStrategy.NO_TRANSFORM


class NameSetter(CompilerPass):
    def __init__(self, strategy: Optional[NameTransformStrategy] = None):
        super().__init__()
        self.strategy = strategy

    def _set_default(self) -> None:
        if self.strategy is None:
            settings = self.ctx.settings
            self.strategy = settings.get("name_case", DEFAULT_CASE)

    def visit_block(self, block: Block) -> None:
        self._set_default()
        render_dict = block.render_dict
        render_dict["name"] = normalize_name(block.name, self.strategy)
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        self._set_default()
        render_dict = field.render_dict
        render_dict["name"] = normalize_name(field.name, self.strategy)

    def visit_method(self, method: Method) -> None:
        self._set_default()
        render_dict = method.render_dict
        render_dict["name"] = normalize_name(method.name, self.strategy)
        method.name = normalize_name(method.name, self.strategy)
