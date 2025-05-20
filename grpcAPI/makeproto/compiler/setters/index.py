from typing import Optional, Set

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode
from grpcAPI.makeproto.protoblock import Block, Field, Method, is_enum


class IndexSetter(CompilerPass):

    def __init__(
        self, reserveds: Optional[Set[int]] = None, counter: Optional[int] = None
    ) -> None:
        super().__init__()
        self.reserveds = reserveds or set()
        self.counter = counter or 1

    def reset(self) -> None:
        self.reserveds.clear()
        self.counter = 1

    def _get_used(self, block: Block) -> None:
        for item in block.fields:
            if isinstance(item, Block):
                self._get_used(item)
            elif item.index is not None:
                self.reserveds.add(item.index)

    def visit_block(self, block: Block) -> None:
        if is_enum(block):
            return
        self.reserveds.update(block.reserved_indexes)
        self._get_used(block)
        try:
            for field in block.fields:
                field.accept(self)
            block.fields.sort(key=lambda x: x.index)
        except Exception as e:
            report = self.ctx.get_report(block.name)
            report.report_error(CompileErrorCode.SETTER_PASS_ERROR, block.name, str(e))

    @property
    def next(self) -> int:
        i = self.counter
        while i in self.reserveds:
            i += 1
        self.counter = i + 1
        return i

    def visit_field(self, field: Field) -> None:
        if field.index is None:
            render_dict = field.render_dict
            next_index = self.next
            field.number = next_index
            render_dict["number"] = str(next_index)

    def visit_method(self, method: Method) -> None:
        pass
