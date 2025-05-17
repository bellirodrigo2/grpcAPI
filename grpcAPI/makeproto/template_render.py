from functools import singledispatch
from pathlib import Path
from typing import Any, Callable, Dict, Optional, get_args, get_origin

from jinja2 import Environment, FileSystemLoader
from typing_extensions import Annotated

from grpcAPI.makeproto.block_models import Block, Field, Method, ProtoBlocks
from grpcAPI.makeproto.protoobj.base import EnumValue, ProtoOption
from grpcAPI.makeproto.protoobj.types import (
    DEFAULT_PRIMITIVES,
    BaseProto,
    allowed_map_key,
)


def get_type(bt: type[Any]) -> Optional[str]:
    if isinstance(bt, type) and issubclass(bt, BaseProto):  # type: ignore
        return bt.prototype()

    return DEFAULT_PRIMITIVES.get(bt, None)


def get_type_str(bt: type[Any]) -> Optional[str]:
    origin = get_origin(bt)
    args = get_args(bt)

    if origin is Annotated:
        return get_type_str(args[0])

    if origin is list:
        type_str = get_type(args[0])
        if type_str is None:
            return None
        return f"repeated {type_str}"

    if origin is dict:
        key_type, value_type = args
        key_type_str = get_type(key_type)
        value_type_str = get_type(value_type)

        if (
            key_type_str is None
            or value_type_str is None
            or key_type not in allowed_map_key
        ):
            return None

        return f"map<{key_type_str}, {value_type_str}>"

    return get_type(bt)


@singledispatch
def render_obj(obj: Any) -> str:
    raise TypeError(f'Cannot render object of type "{type(obj).__name__}"')


@render_obj.register
def _(temp: Field) -> str:
    temp_dict: Dict[str, Any] = temp.to_dict()
    if temp_dict["ftype"] is not None:
        temp_dict["ftype"] = get_type_str(temp_dict["ftype"])
    return field_template.render(temp_dict)


@render_obj.register
def _(temp: Method) -> str:
    temp_dict: Dict[str, Any] = temp.to_dict()
    temp_dict["request_type"] = temp_dict["request_type"].__name__
    temp_dict["response_type"] = temp_dict["response_type"].__name__
    return method_template.render(temp_dict)


@render_obj.register
def _(temp: Block) -> str:
    rendered_items = [render_obj(f) for f in temp.fields]
    return block_template.render(
        description=temp.description,
        template={"block": temp.block_type, "name": temp.name},
        fields=rendered_items,
        options=temp.options or {},
    )


def render_block(block: Block) -> str:

    if not block.fields:
        raise ValueError(f"Rendering Block '{block.name}' is empty.")
    rendered_items = [render_obj(item) for item in block.fields]  # type: ignore

    return block_template.render(
        description=block.description,
        template={"block": block.block_type, "name": block.name},
        fields=rendered_items,
        options=block.options or {},
        reserved_index=block.reserved_index,
        reserved_keys=block.reserved_keys,
    )


def render_protofile(proto_file: ProtoBlocks) -> str:
    rendered_blocks = [render_block(block) for block in proto_file.blocks]  # type: ignore

    return proto_template.render(
        version=3,
        package_name=proto_file.package,
        options=proto_file.options or {},
        blocks=rendered_blocks,
    )


def make_env(path: Path, filters: dict[str, Callable[..., Any]]) -> Environment:

    env = Environment(
        loader=FileSystemLoader(str(path)), trim_blocks=True, lstrip_blocks=True
    )
    for k, v in filters.items():
        env.filters[k] = v  # type: ignore
    return env


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def format_option(item: ProtoOption) -> str:

    key, value = item

    if isinstance(value, bool):  # type: ignore
        val_txt = "true" if value else "false"
    elif isinstance(value, (int, float)):
        val_txt = str(value)
    elif isinstance(value, EnumValue):
        val_txt = str(value)  # sem aspas
    else:
        val_txt = f'"{value}"'  # string literal

    return f"{key} = {val_txt}"


def format_description(raw_description: str, line_limit: int = 80) -> str:
    stripped = raw_description.strip()
    if stripped.startswith("//"):
        return stripped
    if stripped.startswith("/*") and stripped.endswith("*/"):
        return stripped
    if stripped.startswith("/*") and not stripped.endswith("*/"):
        return stripped + " */"
    if "\n" not in stripped and len(stripped) <= line_limit:
        return f"// {stripped}"
    lines = stripped.splitlines()
    cleaned_lines = [line.strip() for line in lines]
    block = "\n".join(f" * {line}" for line in cleaned_lines)
    return f"/*\n{block}\n */"


filters: dict[str, Callable[..., Any]] = {
    "format_option": format_option,
    "format_description": format_description,
}
env = make_env(TEMPLATES_DIR, filters)

field_template = env.get_template("field.j2")
block_template = env.get_template("block.j2")
method_template = env.get_template("method.j2")
proto_template = env.get_template("protofile.j2")
