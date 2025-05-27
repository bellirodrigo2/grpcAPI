from typing import Any, Dict, Literal, Union

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, Field
from grpcAPI.types.base import EnumValue

OptionLevel = Literal["file", "message", "enum", "service", "field", "method"]


def define_field_type(field: Field) -> OptionLevel:
    pass


def define_block_type(block: Block) -> OptionLevel:
    pass


def is_valid(
    tgt: Union[Block, Field],
    # level: Literal["file", "message", "enum", "service", "field", "method"],
    key: str,
    value: Union[str, bool, EnumValue],
) -> bool:
    return False


class OptionsValueValidator(CompilerPass):
    def __init__(self, valid_options: Dict[str, Any]) -> None:
        super().__init__()
        self.valid_options = valid_options


# import json

# with open("valid_options.json", "r") as f:
#     VALID_OPTIONS = json.load(f)


# def validate_option_value(option_name: str, value: str, block_type: str) -> bool:
#     options_for_block = VALID_OPTIONS.get(block_type, {})
#     expected = options_for_block.get(option_name)
#     if not expected:
#         raise ValueError(f"Option '{option_name}' is not valid in {block_type} blocks.")

#     if isinstance(expected, dict) and expected.get("type") == "enum":
#         allowed_values = expected["values"]
#         if value not in allowed_values:
#             raise ValueError(
#                 f"Invalid value '{value}' for enum option '{option_name}' in {block_type}. Allowed: {allowed_values}"
#             )
#     elif expected == "boolean":
#         if value.lower() not in ("true", "false", "1", "0"):
#             raise ValueError(
#                 f"Value '{value}' for option '{option_name}' in {block_type} must be a boolean (true/false)."
#             )
#     elif expected == "string":
#         # simples validação
#         if not isinstance(value, str):
#             raise ValueError(
#                 f"Value for option '{option_name}' in {block_type} must be a string."
#             )
#     else:
#         raise ValueError(
#             f"Unexpected validation rule for option '{option_name}' in {block_type}."
#         )
#     return True
