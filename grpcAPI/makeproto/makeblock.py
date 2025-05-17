from collections import defaultdict
from typing import Dict, List

from grpcAPI.makeproto.block_models import Block, Field
from grpcAPI.makeproto.protoobj.base import FieldSpec, OneOf
from grpcAPI.makeproto.protoobj.message import BaseMessage, get_headers
from grpcAPI.makeproto.reserved import extract_reserveds
from grpcAPI.mapclass import map_class_fields


def make_msgblock(cls: type[BaseMessage]) -> Block:

    protofile, package, description, options, reserveds = get_headers(cls)
    reserved_index, reserved_keys = extract_reserveds(reserveds)

    block = Block(
        protofile=protofile,
        package=package,
        name=cls.__name__,
        block_type="message",
        fields=[],
        description=description,
        options=options,
        reserved_index=reserved_index,
        reserved_keys=reserved_keys,
    )

    fields: List[Block] = []
    oneofs: Dict[str, List[Field]] = defaultdict(list)
    args = map_class_fields(cls, False)
    for arg in args:
        spec = arg.getinstance(FieldSpec, True)
        if spec is None:
            spec = FieldSpec()

        field = Field(
            name=arg.name,
            ftype=arg.basetype,
            description=spec.description,
            options=spec.options,
            number=spec.index,
            block=block,
        )

        if isinstance(spec, OneOf):
            key = spec.key
            oneofs[key].append(field)
        else:
            fields.append(field)

    for k, v in oneofs.items():
        # How to pick description and reserveds from oneof ?
        # If implemented, the main block reserved has got to accumulate those
        ootemp = Block(
            protofile=protofile,
            package=package,
            name=k,
            block_type="oneof",
            fields=v,
            description="",
            options={},
            reserved_index=[],
            reserved_keys=[],
        )
        fields.append(ootemp)

    block.fields = fields

    return block


def make_enumblock(
    enum: type[BaseMessage], default_protofile: str, default_package: str
) -> Block:

    protofile, package, description, options, reserveds = get_headers(enum)
    reserved_index, reserved_keys = extract_reserveds(reserveds)

    enum_block: Block = Block(
        protofile=protofile,
        package=package,
        name=enum.__name__,
        block_type="enum",
        fields=[],
        description=description,
        options=options,
        reserved_index=reserved_index,
        reserved_keys=reserved_keys,
    )

    fields: List[Field] = []
    for member in enum:
        name, value = member.name, member.value
        fields.append(
            Field(
                name=name,
                number=value,
                ftype=None,
                description="",
                options={},
                block=enum_block,
            )
        )

    enum_block.fields = fields

    return enum_block
