from typing import Any, Optional, get_args, get_origin

from grpcAPI.makeproto.block_models import Block
from grpcAPI.makeproto.compiler.compiler import CompilerPass, Field
from grpcAPI.makeproto.compiler.report import CompileErrorCode, CompileReport
from grpcAPI.makeproto.protoobj.base import BaseProto
from grpcAPI.makeproto.protoobj.types import DEFAULT_PRIMITIVES, allowed_map_key


class FieldTypeValidator(CompilerPass):

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        report: CompileReport = self.ctx.get_report(field.block.name)

        if field.block.block_type == "enum":
            # Enum must have no type
            if field.ftype is not None:
                report.report_error(
                    code=CompileErrorCode.ENUM_FIELD_HAS_TYPE,
                    location=field.name,
                    override_msg=f"Enum field '{field.name}' must not have a type. Found {field.ftype}",
                )
            return

        # Non-enum: ftype must be valid
        error = self._check_arg(field.ftype, field.name)
        if error:
            report.report_error(
                code=CompileErrorCode.FIELD_TYPE_INVALID,
                location=field.name,
                override_msg=str(error),
            )

    def _check_arg(self, bt: Optional[type[Any]], name: str) -> Optional[TypeError]:
        if bt is None:
            return TypeError(f'Field "{name}" has no type annotation')

        origin = get_origin(bt)
        args = get_args(bt)

        if origin is list:
            return self._check_type(args[0], name)

        if origin is dict:
            key_type, val_type = args
            if key_type in allowed_map_key:
                return self._check_type(val_type, name)
            return TypeError(
                f'Field "{name}" is a dict with not allowed key type. Found "{key_type}" as dict key'
            )

        return self._check_type(bt, name)

    def _check_type(self, bt: Any, name: str) -> Optional[TypeError]:
        # bt pode ser qualquer coisa
        if not isinstance(bt, type):
            return TypeError(f'Field "{name}" is not a type. Found {bt}')

        if issubclass(bt, BaseProto):  # se for mensagem protobuf pura
            return None

        if bt not in DEFAULT_PRIMITIVES:
            return TypeError(f'Field "{name}" type is not allowed. Found {bt}')

        return None
