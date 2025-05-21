from collections import defaultdict
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional

from grpcAPI.makeproto.protoblock import (
    Block,
    EnumBlock,
    EnumField,
    Field,
    MessageBlock,
    Method,
    Node,
    OneOfBlock,
    OneOfField,
    ServiceBlock,
)
from grpcAPI.mapclass import FuncArg, map_func_args, map_model_fields
from grpcAPI.types import BaseMessage, Metadata, OneOf, ProtoOption, get_headers


def make_msgblock(cls: type[BaseMessage]) -> Block:

    protofile, package, description, options, reserveds = get_headers(cls)

    block = MessageBlock(
        protofile=protofile,
        package=package,
        name=cls.__name__,
        fields=[],
        block=None,
        description=description,
        options=options,
        number=0,
        reserveds=reserveds,
        render_dict={},
    )

    fields: List[Node] = []
    oneofs: Dict[str, List[Field]] = defaultdict(list)
    args = map_model_fields(cls, False)
    for arg in args:
        metadata = arg.getinstance(Metadata, True)
        if metadata is None:
            metadata = Metadata()

        field = Field(
            name=arg.name,
            ftype=arg.basetype,
            description=metadata.description,
            options=metadata.options,
            number=metadata.index,
            block=block,
            render_dict={},
        )

        if isinstance(metadata, OneOf):
            key = metadata.key
            field_dict = asdict(field)
            oneof_field = OneOfField(**field_dict, key=key)
            oneofs[key].append(oneof_field)
        else:
            fields.append(field)

    for k, v in oneofs.items():
        # How to pick description and reserveds from oneof ?
        # If implemented, the main block reserved has got to accumulate those
        ootemp = OneOfBlock(
            protofile=protofile,
            package=package,
            name=k,
            number=0,
            block=block,
            fields=v,
            description="",
            options={},
            reserveds=[],
            render_dict={},
        )
        fields.append(ootemp)

    block.fields = fields

    return block


def make_enumblock(enum: type[BaseMessage]) -> Block:

    protofile, package, description, options, reserveds = get_headers(enum)

    enum_block = EnumBlock(
        protofile=protofile,
        package=package,
        name=enum.__name__,
        fields=[],
        block=None,
        number=0,
        description=description,
        options=options,
        reserveds=reserveds,
        render_dict={},
    )

    fields: List[Field] = []
    for member in enum:
        name, value = member.name, member.value
        fields.append(
            EnumField(
                name=name,
                number=value,
                ftype=None,
                description="",
                options={},
                block=enum_block,
                render_dict={},
            )
        )

    enum_block.fields = fields

    return enum_block


def make_method(
    func: Callable[..., Any],
    ignore_instance: List[type[Any]],
    block: Optional[ServiceBlock] = None,
) -> Method:

    args, returntype = map_func_args(func)

    def has_any(arg: FuncArg, ignore_instance: List[type[Any]]) -> bool:
        return any(arg.hasinstance(bt) for bt in ignore_instance)

    req_types = [arg.basetype for arg in args if not has_any(arg, ignore_instance)]

    return Method(
        name=func.__name__,
        request_type=req_types,
        response_type=returntype.basetype,
        block=block,
        method_func=func,
        number=0,
        description="",
        options=ProtoOption(),
        render_dict={},
    )


def make_service(
    servicename: str,
    protofile: str,
    package: str,
    methods: List[Callable[..., Any]],
    ignore_instance: List[type[Any]],
    description: str,
    options: ProtoOption,
) -> ServiceBlock:

    service = ServiceBlock(
        name=servicename,
        protofile=protofile,
        package=package,
        fields=[],
        number=0,
        block=None,
        options=options,
        description=description,
        render_dict={},
        reserveds=[],
    )
    method_list = [make_method(method, ignore_instance, service) for method in methods]
    service.fields = method_list
    return service
