from typing import Union

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass


class OptionsValidator(CompilerPass):
    def _visit(self, item: Union[Block, Field, Method]) -> None:
        kind = (
            "block"
            if isinstance(item, Block)
            else "field" if isinstance(item, Field) else "method"
        )
        report = self.ctx.get_report(
            item.name if isinstance(item, Block) else item.block.name
        )

        if not isinstance(item.options, dict):
            report.add_error(
                item.name,
                f"{kind.capitalize()} '{item.name}' options must be a dict. Found {type(item.options).__name__}",
                code=self._error_code(kind, "options"),
            )
            return

        for k, v in item.options.items():
            if not isinstance(k, str):
                report.add_error(
                    item.name,
                    f"{kind.capitalize()} '{item.name}' option key must be a string. Found {type(k).__name__}",
                    code=self._error_code(kind, "option_key"),
                )
            if not isinstance(v, (str, bool)):
                report.add_error(
                    item.name,
                    f"{kind.capitalize()} '{item.name}' option value must be string or bool. Found {type(v).__name__}",
                    code=self._error_code(kind, "option_value"),
                )

    def _error_code(self, kind: str, issue: str) -> str:
        base = {
            "block": "E51",
            "field": "E52",
            "method": "E53",
        }[kind]

        suffix = {
            "options": "2",
            "option_key": "3",
            "option_value": "4",
        }[issue]

        return f"{base}{suffix}"

    def visit_block(self, block: Block) -> None:
        self._visit(block)
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        self._visit(field)

    def visit_method(self, method: Method) -> None:
        self._visit(method)
