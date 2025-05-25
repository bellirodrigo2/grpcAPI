# import "common.proto";
# import "pack1/file2.proto";
# import "pack2/file2.proto";

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, EnumField, Field
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.types.types import DEFAULT_PRIMITIVES, BaseField


class ImportsSetter(CompilerPass):

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        if isinstance(field, EnumField):
            return
        try:
            ftype = field.ftype
            if ftype in DEFAULT_PRIMITIVES or isinstance(ftype, BaseField):
                return

            ftype_pack = ftype.package()
            ftype_proto = ftype.protofile()
            block_pack = field.block.package
            block_proto = field.block.protofile

            import_str = None
            if ftype_pack != block_pack:
                # different packages
                import_str = f"{ftype_pack}/{ftype_proto}"
            elif ftype_proto != block_proto:
                # Same package, different file
                import_str = f"{ftype_proto}"
            else:
                # No import
                return

            render_dict = field.block.render_dict
            if "imports" not in render_dict:
                render_dict["imports"] = set()
            render_dict["imports"].add(import_str)
        except Exception as e:
            report: CompileReport = self.ctx.get_report(field.block.name)
            report.report_error(
                CompileErrorCode.SETTER_PASS_ERROR,
                field.name,
                f"ImportsSetter: {str(e)}",
            )
