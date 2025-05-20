from typing import List, Optional

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode
from grpcAPI.makeproto.protoblock import Block, Field, Method, is_enum


class IndexSetter(CompilerPass):

    def __init__(
        self, reserveds: Optional[List[int]] = None, counter: Optional[int] = None
    ) -> None:
        super().__init__()
        self.reserveds = reserveds or []
        self.counter = counter or 1

    def reset(self) -> None:
        self.reserveds.clear()
        self.counter = 1

    def visit_block(self, block: Block) -> None:
        report = self.ctx.get_report(block.name)
        if is_enum(block):
            return
        try:
            for field in block.fields:
                field.accept(self)
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
