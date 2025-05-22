from typing import List

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, Field, Method


def format_description(text: str, max_chars: int) -> str:
    text = text.strip()
    if text.startswith("//") or (text.startswith("/*") and text.endswith("*/")):
        return text
    if text.startswith("/*") and not text.endswith("*/"):
        return text + " */"
    if len(text) <= max_chars:
        return "// " + text
    lines: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        lines.append(text[start:end])
        start = end
    multiline_comment = "/*\n" + "\n".join(lines) + "\n*/"
    return multiline_comment


# def format_description(raw_description: str, line_limit: int = 80) -> str:
#     if "\n" not in stripped and len(stripped) <= line_limit:
#         return f"// {stripped}"
#     lines = stripped.splitlines()
#     cleaned_lines = [line.strip() for line in lines]
#     block = "\n".join(f" * {line}" for line in cleaned_lines)
#     return f"/*\n{block}\n */"


MAXCHAR_PER_LINE = 80


class NameNormalizer(CompilerPass):
    def __init__(self, maxcharlines: int = MAXCHAR_PER_LINE):
        super().__init__()
        self.maxcharlines = maxcharlines

    def set_default(self) -> None:
        settings = self.ctx.settings
        self.maxcharlines = settings.get("max_char_per_line", self.maxcharlines)

    def visit_block(self, block: Block) -> None:
        description = format_description(block.description, self.maxcharlines)
        block.render_dict["description"] = description
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        description = format_description(field.description, self.maxcharlines)
        field.render_dict["description"] = description

    def visit_method(self, method: Method) -> None:
        description = format_description(method.description, self.maxcharlines)
        method.render_dict["description"] = description
