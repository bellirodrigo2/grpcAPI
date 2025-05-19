from typing import Set

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode, CompileReport


class IndexValidator(CompilerPass):

    def __init__(self) -> None:
        super().__init__()
        self.used: Set[int] = set()

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def is_in_index_range(self, index: int, min_: int) -> bool:
        return min_ <= index <= 536870911

    def visit_field(self, field: Field) -> None:
        index = field.number
        name = field.name
        reserveds = field.block.reserved_indexes
        report = self.ctx.get_report(field.block.name)

        if not isinstance(index, int):  # type: ignore
            report.report_error(code=CompileErrorCode.INVALID_INDEX_TYPE, location=name)
        elif index in reserveds:
            report.report_error(
                code=CompileErrorCode.DUPLICATE_INDEX,
                location=name,
                override_msg=f"'{index}' is reserved",
            )
        elif index in self.used:
            report.report_error(
                code=CompileErrorCode.DUPLICATE_INDEX,
                location=name,
            )
        elif not self.is_in_index_range(index, 1 if not field.ftype else 0):
            report.report_error(code=CompileErrorCode.INDEX_OUT_OF_RANGE, location=name)
        else:
            self.used.add(index)

    def visit_method(self, method: Method) -> None:
        pass


class ReservedValidator(CompilerPass):
    def __init__(self, report: CompileReport):
        self.report = report

    def _min_index(self, block: Block) -> int:
        return 1 if block.block_type in ("message", "oneof") else 0

    def _max_index(self) -> int:
        return 536870911

    def visit_block(self, block: Block) -> None:
        reserved_index = block.reserved_index

        min_index = self._min_index(block)
        max_index = self._max_index()

        for item in reserved_index:
            if isinstance(item, int):
                values = [item]
            else:
                values = list(item)

            for val in values:
                if not isinstance(val, int):  # type: ignore
                    self.report.add_error(
                        block.name,
                        f"Invalid reserved index type: {val} ({type(val)})",
                        code="E201",
                    )
                elif not (min_index <= val <= max_index):
                    self.report.add_error(
                        block.name,
                        f"Reserved index {val} out of range for block type '{block.block_type}'",
                        code="E202",
                    )

        # Recursivamente validar sub-blocks
        for field in block.fields:
            field.accept(self)
