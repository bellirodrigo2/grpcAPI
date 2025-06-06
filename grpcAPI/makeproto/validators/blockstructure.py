from typing import Callable, Dict

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import (
    Block,
    EnumBlock,
    MessageBlock,
    OneOfBlock,
    ServiceBlock,
)
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport


def validate_service(block: Block, report: CompileReport) -> None: ...


def validate_enum(block: Block, report: CompileReport) -> None:
    if len(block.fields) == 0:
        report.report_error(CompileErrorCode.ENUM_MUST_HAVE_FIELDS, location=block.name)


def validate_message(block: Block, report: CompileReport) -> None: ...


def validate_oneof(block: Block, report: CompileReport) -> None:
    if len(block.fields) == 0:
        report.report_error(
            CompileErrorCode.ONEOF_MUST_HAVE_FIELDS, location=block.name
        )


validate_map: Dict[Block, Callable[[Block, CompileReport], None]] = {
    ServiceBlock: validate_service,
    EnumBlock: validate_enum,
    MessageBlock: validate_message,
    OneOfBlock: validate_oneof,
}


def wrong_validation(block: Block, report: CompileReport) -> None:
    raise NotImplementedError(
        f'At Block "{block.name}", no implementation found for block structure validation type: "{type(block).__name__}"'
    )


class BlockStructureValidator(CompilerPass):

    def visit_block(self, block: Block) -> None:
        report: CompileReport = self.ctx.get_report(block.name)
        validate = validate_map.get(type(block), wrong_validation)
        validate(block, report)

        for field in block.fields:
            field.accept(self)  # run message internal oneofs
            if field.block != block:
                report.report_error(
                    CompileErrorCode.UNLINKED_FIELD, location=field.name
                )
