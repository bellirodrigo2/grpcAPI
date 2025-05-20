from typing import List

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode


class IndexSetter(CompilerPass):

    def __init__(self) -> None:
        super().__init__()
        self._reset()

    def _reset(self) -> None:
        self.reserveds: List[int] = []
        self.counter = 1

    def visit_block(self, block: Block) -> None:
        report = self.ctx.get_report(block.name)
        if block.block_type == "enum":
            return
        try:
            for field in block.fields:
                field.accept(self)

            if block.block_type == "message":
                self._reset()
                block.fields.sort(key=lambda x: x.number)
        except Exception as e:
            report.report_error(CompileErrorCode.SETTER_PASS_ERROR, block.name, str(e))

    @property
    def next(self) -> int:
        i = self.counter
        while i in self.reserveds:
            i += 1
        self.counter = i + 1
        return i

    def visit_field(self, field: Field) -> None:
        if field.number is None:
            render_dict = field.render_dict
            next_index = self.next
            field.number = next_index
            render_dict["number"] = str(next_index)

    def visit_method(self, method: Method) -> None:
        pass
