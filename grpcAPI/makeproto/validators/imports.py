from typing import Any, Optional, Set, Tuple, Type, Union, get_args, get_origin

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, EnumField, Field
from grpcAPI.makeproto.report import CompileErrorCode
from grpcAPI.types import DEFAULT_PRIMITIVES, _NoPackage
from grpcAPI.types.types import BaseField


def get_type(bt: Type[Any]) -> Type[Any]:

    if get_origin(bt) in {list, dict}:
        return get_args(bt)[0]
    return bt


class ImportsValidator(CompilerPass):

    def __init__(
        self,
        key: Optional[object] = None,
        packset: Optional[Set[Tuple[Union[str, _NoPackage], str]]] = None,
    ) -> None:
        super().__init__()
        self._packset = packset
        self._key = key

    def set_default(self) -> None:
        if self._packset is None:
            self._packset = self.ctx.get_state(self._key)
        if self._packset is None:
            raise ValueError(
                f'Compiler Context must have a packages set on state with a given key: "{self._key}"'
            )

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        if isinstance(field, EnumField):
            return
        ftype = get_type(field.ftype)
        if ftype in DEFAULT_PRIMITIVES or issubclass(ftype, BaseField):
            return
        # BaseMessage or Enum (guaranteed by type validator)
        ftype_pack = ftype.package()
        try:
            ftype_proto = ftype.protofile()
        except NotImplementedError:
            # protofile not implemented is covered in types validator
            return

        if (ftype_pack, ftype_proto) not in self._packset:
            report = self.ctx.get_report(field.top_block.name)
            report.report_error(
                CompileErrorCode.OBJECT_MODULE_NOT_FOUND,
                location=field.top_block.name,
                override_msg=f"Field {field.name} object Module ({ftype_pack}/{ftype_proto}) is not mapped",
            )
