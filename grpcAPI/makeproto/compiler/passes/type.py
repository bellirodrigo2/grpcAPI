from typing import Any, Optional, get_args, get_origin

from grpcAPI.makeproto.block_models import Field
from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.protoobj.base import BaseProto
from grpcAPI.makeproto.protoobj.types import DEFAULT_PRIMITIVES, allowed_map_key


class FieldTypeValidator(CompilerPass):
    def visit_field(self, field: Field) -> None:
        report = self.ctx.get_report(field.block.name)

        if field.block.block_type == "enum":
            # Enum must have no type
            if field.ftype is not None:
                report.add_error(
                    field.name,
                    f"Enum field '{field.name}' must not have a type. Found {field.ftype}",
                    code="E620",
                )
            return

        # Non-enum: ftype must be valid
        error = self._check_arg(field.ftype, field.name)
        if error:
            report.add_error(field.name, str(error), code="E621")

    def _check_arg(self, bt: Optional[type[Any]], name: str) -> Optional[TypeError]:
        if bt is None:
            return TypeError(f'Field "{name}" has no type annotation')

        origin = get_origin(bt)
        args = get_args(bt)

        if origin is list:
            return self._check_type(args[0], name)

        if origin is dict:
            if args[0] in allowed_map_key:
                return self._check_type(args[1], name)
            return TypeError(
                f'Field "{name}" is a dict with not allowed key type. Found "{args[0]}" as dict key'
            )

        return self._check_type(bt, name)

    def _check_type(self, bt: type[Any], name: str) -> Optional[TypeError]:
        if not isinstance(bt, type):  # type: ignore
            return TypeError(f'Field "{name}" is not a type. Found {bt}')

        if issubclass(bt, BaseProto):  # type: ignore
            return None

        if bt not in DEFAULT_PRIMITIVES:
            return TypeError(f'Field "{name}" type is not allowed. Found {bt}')

        return None
