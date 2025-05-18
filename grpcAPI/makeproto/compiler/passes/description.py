from typing import Optional, Union

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass


class DescriptionValidator(CompilerPass):
    def _visit(self, item: Union[Block, Field, Method]) -> None:
        kind = (
            "block"
            if isinstance(item, Block)
            else "field" if isinstance(item, Field) else "method"
        )
        report = self.ctx.get_report(
            item.name if isinstance(item, Block) else item.block.name
        )

        if not isinstance(item.description, str):
            report.add_error(
                item.name,
                f"{kind.capitalize()} '{item.name}' has invalid description type: {type(item.description).__name__}",
                code=self._error_code(kind),
            )

    def _error_code(self, kind: str) -> str:
        return {
            "block": "E411",
            "field": "E421",
            "method": "E431",
        }[kind]

    def visit_block(self, block: Block) -> None:
        self._visit(block)
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        self._visit(field)

    def visit_method(self, method: Method) -> None:
        self._visit(method)


def format_description(text: str, max_chars: int) -> str:
    text = text.strip()

    if text.startswith("//") or (text.startswith("/*") and text.endswith("*/")):
        return text

    if len(text) <= max_chars:
        return "// " + text

    lines = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        lines.append(text[start:end])
        start = end

    multiline_comment = "/*\n" + "\n".join(lines) + "\n*/"
    return multiline_comment


MAXCHAR_PER_LINE = 80


class NameNormalizer(CompilerPass):
    def __init__(self, maxcharlines: Optional[int] = None):
        self.maxcharlines = maxcharlines

    def _set_default(self) -> None:
        if self.maxcharlines is None:
            settings = self.ctx.settings
            self.maxcharlines = settings.get("max_char_per_line", MAXCHAR_PER_LINE)

    def visit_block(self, block: "Block") -> None:
        self._set_default()
        block.name = format_description(block.name, self.maxcharlines)
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: "Field") -> None:
        self._set_default()
        field.name = format_description(field.name, self.maxcharlines)

    def visit_method(self, method: "Method") -> None:
        self._set_default()
        method.name = format_description(method.name, self.maxcharlines)
