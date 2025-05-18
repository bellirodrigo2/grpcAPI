from typing import List, Set

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileReport


class IndexValidator(CompilerPass):
    def __init__(self, report: CompileReport, reserved: List[int]):
        self.report = report
        self.used: Set[int] = set()
        self.reserveds = reserved

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def is_in_index_range(self, index: int, min_: int) -> bool:
        return min_ <= index <= 536870911

    def visit_field(self, field: Field) -> None:
        index = field.number
        name = field.name

        if not isinstance(index, int):  # type: ignore
            self.report.add_error(
                name,
                f"On Field '{name}', Index has wrong type: {index}",
                code="E201",
            )

        elif index in self.reserveds:
            self.report.add_error(
                name, f"On Field '{name}', duplicate index: {index}", code="E202"
            )
        elif not self.is_in_index_range(index, 0 if not field.ftype else 1):
            self.report.add_error(
                name,
                f"On Field '{name}', index out of range, got {index}",
                code="E203",
            )
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
