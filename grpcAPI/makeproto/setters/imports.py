# import "common.proto";
# import "pack1/file2.proto";
# import "pack2/file2.proto";

from typing import Any, Optional, Type, get_args, get_origin

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, EnumField, Field
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.types.method import if_stream_get_type
from grpcAPI.types.types import DEFAULT_PRIMITIVES, BaseField


def get_type(bt: Type[Any]) -> Type[Any]:

    if get_origin(bt) in {list, dict}:
        return get_args(bt)[0]
    return bt


def get_func_arg(bt: Type[Any]) -> Type[Any]:
    basetype = if_stream_get_type(bt)
    return basetype or bt


class ImportsSetter(CompilerPass):

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def _get_imports(
        self, ftype: Type[Any], block_package: str, block_protofile: str
    ) -> Optional[str]:

        if ftype in DEFAULT_PRIMITIVES or issubclass(ftype, BaseField):
            return None
        ftype_pack = ftype.package()
        ftype_proto = ftype.protofile()
        block_pack = block_package
        block_proto = block_protofile
        import_str = None
        if ftype_pack != block_pack:
            # different packages
            import_str = f"{ftype_pack}/{ftype_proto.removesuffix('.proto')}.proto"
        elif ftype_proto != block_proto:
            # Same package, different file
            import_str = f"{ftype_proto}"
        return import_str

    def _set_imports(self, field: Field, ftype: Type[Any]) -> None:
        try:
            import_str = self._get_imports(
                ftype, field.block.package, field.block.protofile
            )
            if import_str is None:
                return
            module = self.ctx.get_state(field.top_block.protofile)
            module.imports.add(import_str)
        except Exception as e:
            report: CompileReport = self.ctx.get_report(field.block.name)
            report.report_error(
                CompileErrorCode.SETTER_PASS_ERROR,
                field.name,
                f"ImportsSetter: {str(e)}",
            )

    def visit_field(self, field: Field) -> None:
        if isinstance(field, EnumField):
            return

        ftype = get_type(field.ftype)
        self._set_imports(field, ftype)

    def visit_method(self, method: Any) -> None:

        request_type = get_func_arg(method.request_type[0])
        self._set_imports(method, request_type)
        response_type = get_func_arg(method.response_type)
        self._set_imports(method, response_type)
