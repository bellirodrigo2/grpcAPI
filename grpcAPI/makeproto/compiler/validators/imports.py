# import "common.proto";
# import "pack1/file2.proto";
# import "pack2/file2.proto";

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode
from grpcAPI.makeproto.protoblock import Block, EnumField, Field
from grpcAPI.types.types import DEFAULT_PRIMITIVES, BaseField


class ImportsValidator(CompilerPass):

    def __init__(self) -> None:
        super().__init__()
        self.packset = None

    def set_default(self) -> None:
        if "_packages" not in self.ctx.state:
            raise ValueError(
                'Compiler Context must have a packages set on state with key "_packages"'
            )
        self.packset = self.ctx.state["_packages"]

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        if isinstance(field, EnumField):
            return
        ftype = field.ftype
        if ftype in DEFAULT_PRIMITIVES or isinstance(ftype, BaseField):
            return
        # BaseMessage or Enum (guaranteed by type validator)
        ftype_pack = ftype.package()
        try:
            ftype_proto = ftype.protofile()
        except NotImplementedError:
            # protofile not implemented is covered in types validator
            return

        if (ftype_pack, ftype_proto) not in self.packset:
            report = self.ctx.get_report(field.top_block.name)
            report.report_error(
                CompileErrorCode.OBJECT_MODULE_NOT_FOUND,
                location=field.top_block.name,
                override_msg=f"Field {field.name} object Module ({ftype_pack}/{ftype_proto}) is not mapped",
            )
