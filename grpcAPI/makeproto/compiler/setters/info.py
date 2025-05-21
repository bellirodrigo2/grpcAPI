import textwrap
from typing import List

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, Field, Method
from grpcAPI.types import EnumValue, ProtoOption


def format_option(options: ProtoOption) -> str:

    str_options: List[str] = []

    for key, value in options.items():
        if isinstance(value, bool):  # type: ignore
            val_txt = "true" if value else "false"
        elif isinstance(value, (int, float)):
            val_txt = str(value)
        elif isinstance(value, EnumValue):
            val_txt = str(value)  # sem aspas
        else:
            val_txt = f'"{value}"'  # string literal

        str_options.append(f"{key} = {val_txt}")
    return ", ".join(str_options)


class OptionsSetter(CompilerPass):

    def visit_block(self, block: Block) -> None:
        options = format_option(block.options)
        block.render_dict["options"] = options
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        options = format_option(field.options)
        field.render_dict["options"] = options

    def visit_method(self, method: Method) -> None:
        options = format_option(method.options)
        method.render_dict["options"] = options


def format_description(text: str, max_chars: int, always_format: bool) -> str:
    text = text.strip()

    if not always_format:
        if text.startswith("//"):
            return text
        if text.startswith("/*") and text.endswith("*/"):
            return text

    text = text.removeprefix("//").strip()
    text = text.removeprefix("/*").strip()
    text = text.removesuffix("*/").strip()

    if len(text) <= max_chars and "\n" not in text:
        return f"// {text}"

    lines: List[str] = textwrap.wrap(text, width=max_chars)
    multiline_comment = "/*\n" + "\n".join(lines) + "\n*/"
    return multiline_comment


MAXCHAR_PER_LINE = 80
ALWAYS_FORMAT = True


class DescriptionSetter(CompilerPass):
    def __init__(
        self, maxcharlines: int = MAXCHAR_PER_LINE, always_format: bool = ALWAYS_FORMAT
    ):
        super().__init__()
        self.maxcharlines = maxcharlines
        self.always_format = always_format

    def set_default(self) -> None:
        settings = self.ctx.settings
        self.maxcharlines = settings.get("max_char_per_line", self.maxcharlines)
        self.always_format = settings.get("always_format", self.always_format)

    def _format(self, text: str) -> str:
        return format_description(text, self.maxcharlines, self.always_format)

    def visit_block(self, block: Block) -> None:
        description = self._format(block.description)
        block.render_dict["description"] = description
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        description = self._format(field.description)
        field.render_dict["description"] = description

    def visit_method(self, method: Method) -> None:
        description = self._format(method.description)
        method.render_dict["description"] = description
