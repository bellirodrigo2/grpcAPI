import re
from typing import Optional, Set

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode, CompileReport
from grpcAPI.makeproto.protoblock import Block, Field, OneOfBlock

VALID_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


PROTOBUF_RESERVED_WORDS = {
    "syntax",
    "import",
    "option",
    "package",
    "message",
    "enum",
    "service",
    "rpc",
    "returns",
    "reserved",
    "repeated",
    "optional",
    "required",
    "map",
    "oneof",
    "extensions",
    "extend",
    "group",
    "true",
    "false",
}


def check_valid(name: str, report: CompileReport) -> None:
    if not VALID_NAME_RE.match(name):
        report.report_error(
            code=CompileErrorCode.INVALID_NAME,
            location=name,
            override_msg=f"Invalid name: '{name}'",
        )
    if name in PROTOBUF_RESERVED_WORDS:
        report.report_error(
            code=CompileErrorCode.RESERVED_NAME,
            location=name,
            override_msg=f"Protobuf reserved name: '{name}'",
        )


class NameValidator(CompilerPass):
    def __init__(
        self,
        used_names: Optional[Set[str]] = None,
        reserved_keys: Optional[Set[str]] = None,
    ) -> None:
        super().__init__()
        self.used_names = used_names or set()
        self.reserved_keys = reserved_keys or set()


class BlockNameValidator(NameValidator):

    def visit_block(self, block: Block) -> None:
        name = block.name
        report = self.ctx.get_report(block.name)
        check_valid(name, report)
        if name in self.used_names:
            report.report_error(
                code=CompileErrorCode.DUPLICATED_NAME,
                location=name,
                override_msg=f"Duplicated Block name '{name}' in the block list",
            )
        else:
            self.used_names.add(name)
        oneofs = [item for item in block.fields if isinstance(item, OneOfBlock)]
        for oneof in oneofs:
            oneof.accept(self)


class FieldNameValidator(NameValidator):
    def reset(self) -> None:
        self.used_names.clear()
        self.reserved_keys.clear()

    def visit_block(self, block: Block) -> None:
        self.reserved_keys.update(block.reserved_keys)
        if isinstance(block, OneOfBlock):
            top_block = block.top_block.name
            report = self.ctx.get_report(top_block)
            check_valid(block.name, report)
            self._check_already_used(top_block, block.name, report)

        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        name = field.name
        blockname = field.top_block.name
        report = self.ctx.get_report(blockname)
        check_valid(name, report)
        self._check_already_used(blockname, name, report)

    def _check_already_used(
        self, blockname: str, name: str, report: CompileReport
    ) -> None:
        if name in self.reserved_keys:
            report.report_error(
                code=CompileErrorCode.NAME_RESERVED_IN_BLOCK,
                location=name,
                override_msg=f"Name '{name}' is reserved in block '{blockname}'",
            )
        elif name in self.used_names:
            report.report_error(
                code=CompileErrorCode.DUPLICATED_NAME,
                location=name,
                override_msg=f"Duplicated name '{name}' in the block '{blockname}'",
            )
        else:
            self.used_names.add(name)
