from typing import Union

from grpcAPI.makeproto.compiler import CompileErrorCode, CompilerPass
from grpcAPI.makeproto.protoblock import Block, Field, Method


class OptionsValidator(CompilerPass):
    def _visit(self, item: Union[Block, Field, Method]) -> None:
        report = self.ctx.get_report(
            item.name if isinstance(item, Block) else item.block.name
        )

        if not isinstance(item.options, dict):  # type: ignore
            report.report_error(
                code=CompileErrorCode.INVALID_OPTIONS, location=item.name
            )
            return

        for k, v in item.options.items():
            if not isinstance(k, str):  # type: ignore
                report.report_error(
                    code=CompileErrorCode.INVALID_KEY_OPTIONS, location=item.name
                )
            if not isinstance(v, (str, bool)):  # type: ignore
                report.report_error(
                    CompileErrorCode.INVALID_VALUE_OPTIONS, location=item.name
                )

    def visit_block(self, block: Block) -> None:
        self._visit(block)
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        self._visit(field)

    def visit_method(self, method: Method) -> None:
        self._visit(method)


class DescriptionValidator(CompilerPass):
    def _visit(self, item: Union[Block, Field, Method]) -> None:
        report = self.ctx.get_report(
            item.name if isinstance(item, Block) else item.block.name
        )

        if not isinstance(item.description, str):
            report.report_error(
                code=CompileErrorCode.INVALID_DESCRIPTION,
                location=item.name,
            )

    def visit_block(self, block: Block) -> None:
        self._visit(block)
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        self._visit(field)

    def visit_method(self, method: Method) -> None:
        self._visit(method)
