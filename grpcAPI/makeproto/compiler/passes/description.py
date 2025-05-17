from typing import Union

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
