from typing import Optional, Set

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode
from grpcAPI.makeproto.protoblock import Block, Field, is_enum, min_enum


def is_in_index_range(index: int, is_enum: bool) -> bool:
    start = min_enum if is_enum else 1
    return start <= index <= 536870911


def is_in_google_range(index: int) -> bool:
    return 19000 <= index <= 19999


class IndexValidator(CompilerPass):

    def __init__(
        self, used: Optional[Set[int]] = None, reserveds: Optional[Set[int]] = None
    ) -> None:
        super().__init__()
        self.used: Set[int] = used or set()
        self.reserveds: Set[int] = reserveds or set()

    def reset(self) -> None:
        self.used.clear()
        self.reserveds.clear()

    def visit_block(self, block: Block) -> None:
        has_zero = False
        for field in block.fields:
            field.accept(self)
            if field.number == 0:
                has_zero = True
        if is_enum(block) and not has_zero:
            report = self.ctx.get_report(block.name)
            report.report_error(
                code=CompileErrorCode.INVALID_ENUM_INDEX, location=block.name
            )

    def visit_field(self, field: Field) -> None:
        index = field.number
        name = field.name
        report = self.ctx.get_report(field.top_block.name)
        is_enum_field = is_enum(field)
        if not is_enum_field and index is None:
            return
        if not isinstance(index, int):  # type: ignore
            report.report_error(code=CompileErrorCode.INVALID_INDEX_TYPE, location=name)
        elif index in self.reserveds:
            report.report_error(
                code=CompileErrorCode.RESERVED_INDEX,
                location=name,
            )
        elif index in self.used:
            report.report_error(
                code=CompileErrorCode.DUPLICATE_INDEX,
                location=name,
            )
        elif not is_in_index_range(index, is_enum_field):
            report.report_error(code=CompileErrorCode.INDEX_OUT_OF_RANGE, location=name)
        elif is_in_google_range(index):
            report.report_error(
                code=CompileErrorCode.RESERVED_INDEX,
                location=name,
                override_msg="Reserved by protobuf",
            )
        else:
            if not is_enum(field.block):
                self.used.add(index)
