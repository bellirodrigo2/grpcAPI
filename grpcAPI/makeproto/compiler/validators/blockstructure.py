from typing import Callable, Dict

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileReport


def validate_service(block: Block, report: CompileReport) -> None:
    for f in block.fields:
        if not isinstance(f, Method):
            report.add_error(
                f.name if hasattr(f, "name") else block.name,
                f"Service Block should have only Methods. Found {type(f)}",
                code="E301",
            )


def validate_enum(block: Block, report: CompileReport) -> None:
    for f in block.fields:
        if not isinstance(f, Field):
            has_name = hasattr(f, "name")
            report.add_error(
                f.name if has_name else block.name,
                f"Enum Block should have only Fields. Found {type(f)}",
                code="E302",
            )
        elif f.ftype:
            report.add_error(
                f.name,
                f"Enum Field should not have a type. Found '{f.ftype}'",
                code="E303",
            )


def validate_message(block: Block, report: CompileReport) -> None:
    for f in block.fields:
        if isinstance(f, Method):
            report.add_error(
                f.name,
                f"Message Block should not have Methods. Found method: {f.name}",
                code="E304",
            )
        elif isinstance(f, Field) and not f.ftype:
            report.add_error(
                f.name,
                f"Message Field must have a type. Found no type for field '{f.name}'",
                code="E305",
            )


def validate_oneof(block: Block, report: CompileReport) -> None:
    for f in block.fields:
        if not isinstance(f, Field):
            report.add_error(
                block.name,
                f"Oneof Block should have only Fields. Found {type(f)}",
                code="E306",
            )
        elif not f.ftype:
            report.add_error(
                f.name,
                f"Oneof Field must have a type. Found no type for field '{f.name}'",
                code="E307",
            )


validate_map: Dict[str, Callable[[Block, CompileReport], None]] = {
    "service": validate_service,
    "enum": validate_enum,
    "message": validate_message,
    "oneof": validate_oneof,
}


def wrong_validation(block: Block, report: CompileReport) -> None:
    raise NotImplementedError(
        f'At Block "{block.name}", no implementation found for block structure validation type: "{block.block_type}"'
    )


class BlockStructureValidator(CompilerPass):

    def visit_block(self, block: Block) -> None:
        report: CompileReport = self.ctx.get_report(block.name)
        validate = validate_map.get(block.block_type, wrong_validation)
        validate(block, report)

    def visit_field(self, field: Field) -> None:
        pass

    def visit_method(self, method: Method) -> None:
        pass

aqui falta checar se todos os fields tem bloco definido