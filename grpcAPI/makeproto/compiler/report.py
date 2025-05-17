from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, NamedTuple, Optional

from rich.console import Console
from rich.table import Table

# ========== DEFINIÇÃO ESTÁTICA DE ERROS ==========


class CompileErrorDetail(NamedTuple):
    code: str
    message: str
    description: str


class CompileErrorCode(Enum):
    # E100 - Nomes
    INVALID_NAME = "E101"
    RESERVED_NAME = "E102"
    NAME_RESERVED_IN_BLOCK = "E103"
    DUPLICATED_NAME = "E104"

    # E200 - Índices
    INVALID_INDEX_TYPE = "E201"
    DUPLICATE_INDEX = "E202"
    INDEX_OUT_OF_RANGE = "E203"

    # E300 - Estrutura dos blocos
    SERVICE_MUST_HAVE_METHODS = "E301"
    ENUM_MUST_HAVE_FIELDS = "E302"
    ENUM_FIELD_SHOULD_NOT_HAVE_TYPE = "E303"
    MESSAGE_SHOULD_NOT_HAVE_METHODS = "E304"
    MESSAGE_FIELD_MISSING_TYPE = "E305"
    ONEOF_MUST_HAVE_FIELDS = "E306"
    ONEOF_FIELD_MISSING_TYPE = "E307"

    # E400 - Descrições
    INVALID_BLOCK_DESCRIPTION = "E411"
    INVALID_FIELD_DESCRIPTION = "E421"
    INVALID_METHOD_DESCRIPTION = "E431"

    # E500 - Opções
    INVALID_BLOCK_OPTIONS = "E512"
    INVALID_BLOCK_OPTION_KEY = "E513"
    INVALID_BLOCK_OPTION_VALUE = "E514"
    INVALID_FIELD_OPTIONS = "E522"
    INVALID_FIELD_OPTION_KEY = "E523"
    INVALID_FIELD_OPTION_VALUE = "E524"
    INVALID_METHOD_OPTIONS = "E532"
    INVALID_METHOD_OPTION_KEY = "E533"
    INVALID_METHOD_OPTION_VALUE = "E534"

    # E600 - Tipagem
    ENUM_FIELD_HAS_TYPE = "E620"
    FIELD_TYPE_INVALID = "E621"

    # E800 - Métodos
    METHOD_INVALID_REQUEST_TYPE = "E801"
    METHOD_INVALID_RESPONSE_TYPE = "E802"
    METHOD_INVALID_DESCRIPTION_TYPE = "E803"
    METHOD_OPTIONS_NOT_DICT = "E804"
    METHOD_OPTION_KEY_NOT_STRING = "E805"
    METHOD_OPTION_VALUE_INVALID = "E806"

    # E999 - Outros
    UNKNOWN_VALIDATION_STRATEGY = "E999"


COMPILE_ERROR_REGISTRY: Dict[CompileErrorCode, CompileErrorDetail] = {
    CompileErrorCode.INVALID_NAME: CompileErrorDetail(
        "E101", "Invalid name", "Name does not match the expected pattern"
    ),
    CompileErrorCode.RESERVED_NAME: CompileErrorDetail(
        "E102", "Reserved name", "Name is a reserved Protobuf keyword"
    ),
    CompileErrorCode.NAME_RESERVED_IN_BLOCK: CompileErrorDetail(
        "E103", "Name reserved in block", "Field name is reserved within this block"
    ),
    CompileErrorCode.DUPLICATED_NAME: CompileErrorDetail(
        "E104", "Duplicated name", "Name is used more than once in the same block"
    ),
    CompileErrorCode.INVALID_INDEX_TYPE: CompileErrorDetail(
        "E201", "Invalid index type", "Field or reserved index must be an integer"
    ),
    CompileErrorCode.DUPLICATE_INDEX: CompileErrorDetail(
        "E202", "Duplicate index", "Index is already used in the block"
    ),
    CompileErrorCode.INDEX_OUT_OF_RANGE: CompileErrorDetail(
        "E203", "Index out of range", "Index is outside the valid range"
    ),
    CompileErrorCode.SERVICE_MUST_HAVE_METHODS: CompileErrorDetail(
        "E301", "Invalid service block", "Service block must contain only methods"
    ),
    CompileErrorCode.ENUM_MUST_HAVE_FIELDS: CompileErrorDetail(
        "E302", "Invalid enum block", "Enum block must contain only fields"
    ),
    CompileErrorCode.ENUM_FIELD_SHOULD_NOT_HAVE_TYPE: CompileErrorDetail(
        "E303", "Enum field has type", "Enum fields must not have explicit types"
    ),
    CompileErrorCode.MESSAGE_SHOULD_NOT_HAVE_METHODS: CompileErrorDetail(
        "E304", "Message with methods", "Message blocks must not contain methods"
    ),
    CompileErrorCode.MESSAGE_FIELD_MISSING_TYPE: CompileErrorDetail(
        "E305", "Field missing type", "Field must declare a type"
    ),
    CompileErrorCode.ONEOF_MUST_HAVE_FIELDS: CompileErrorDetail(
        "E306", "Invalid oneof block", "Oneof blocks must contain only fields"
    ),
    CompileErrorCode.ONEOF_FIELD_MISSING_TYPE: CompileErrorDetail(
        "E307", "Oneof field missing type", "Oneof field must declare a type"
    ),
    CompileErrorCode.INVALID_BLOCK_DESCRIPTION: CompileErrorDetail(
        "E411", "Invalid block description", "Description must be a string"
    ),
    CompileErrorCode.INVALID_FIELD_DESCRIPTION: CompileErrorDetail(
        "E421", "Invalid field description", "Description must be a string"
    ),
    CompileErrorCode.INVALID_METHOD_DESCRIPTION: CompileErrorDetail(
        "E431", "Invalid method description", "Description must be a string"
    ),
    CompileErrorCode.INVALID_BLOCK_OPTIONS: CompileErrorDetail(
        "E512", "Invalid block options", "Options must be a dictionary"
    ),
    CompileErrorCode.INVALID_BLOCK_OPTION_KEY: CompileErrorDetail(
        "E513", "Invalid option key", "Option keys must be strings"
    ),
    CompileErrorCode.INVALID_BLOCK_OPTION_VALUE: CompileErrorDetail(
        "E514", "Invalid option value", "Option values must be string or boolean"
    ),
    CompileErrorCode.INVALID_FIELD_OPTIONS: CompileErrorDetail(
        "E522", "Invalid field options", "Options must be a dictionary"
    ),
    CompileErrorCode.INVALID_FIELD_OPTION_KEY: CompileErrorDetail(
        "E523", "Invalid field option key", "Option keys must be strings"
    ),
    CompileErrorCode.INVALID_FIELD_OPTION_VALUE: CompileErrorDetail(
        "E524", "Invalid field option value", "Option values must be string or boolean"
    ),
    CompileErrorCode.INVALID_METHOD_OPTIONS: CompileErrorDetail(
        "E532", "Invalid method options", "Options must be a dictionary"
    ),
    CompileErrorCode.INVALID_METHOD_OPTION_KEY: CompileErrorDetail(
        "E533", "Invalid method option key", "Option keys must be strings"
    ),
    CompileErrorCode.INVALID_METHOD_OPTION_VALUE: CompileErrorDetail(
        "E534", "Invalid method option value", "Option values must be string or boolean"
    ),
    CompileErrorCode.ENUM_FIELD_HAS_TYPE: CompileErrorDetail(
        "E620", "Enum field has type", "Enum fields should not declare a type"
    ),
    CompileErrorCode.FIELD_TYPE_INVALID: CompileErrorDetail(
        "E621", "Invalid field type", "Type is not supported or not recognized"
    ),
    CompileErrorCode.METHOD_INVALID_REQUEST_TYPE: CompileErrorDetail(
        "E801", "Invalid request type", "Request type is invalid or not a BaseMessage"
    ),
    CompileErrorCode.METHOD_INVALID_RESPONSE_TYPE: CompileErrorDetail(
        "E802", "Invalid response type", "Response type is invalid or not a BaseMessage"
    ),
    CompileErrorCode.METHOD_INVALID_DESCRIPTION_TYPE: CompileErrorDetail(
        "E803", "Invalid description type", "Description must be a string"
    ),
    CompileErrorCode.METHOD_OPTIONS_NOT_DICT: CompileErrorDetail(
        "E804", "Options must be a dict", "Method options must be a dictionary"
    ),
    CompileErrorCode.METHOD_OPTION_KEY_NOT_STRING: CompileErrorDetail(
        "E805", "Option key not string", "Option keys must be strings"
    ),
    CompileErrorCode.METHOD_OPTION_VALUE_INVALID: CompileErrorDetail(
        "E806", "Invalid option value", "Option value must be a string or boolean"
    ),
    CompileErrorCode.UNKNOWN_VALIDATION_STRATEGY: CompileErrorDetail(
        "E999",
        "Unknown validation strategy",
        "No implementation found for the strategy",
    ),
}


# ========== INSTÂNCIA DE ERRO OCORRIDO ==========


@dataclass
class CompileError:
    code: str
    message: str
    location: str


# ========== RELATÓRIO DE COMPILAÇÃO ==========


class CompileReport:
    def __init__(self, name: str) -> None:
        self.name = name
        self.errors: List[CompileError] = []

    def __len__(self) -> int:
        return len(self.errors)

    def is_valid(self) -> bool:
        return not self.errors

    def report_error(
        self,
        code: CompileErrorCode,
        location: str,
        override_msg: Optional[str] = None,
    ) -> None:
        detail = COMPILE_ERROR_REGISTRY[code]
        message = override_msg or detail.message
        self.errors.append(
            CompileError(code=detail.code, message=message, location=location)
        )

    def show(self) -> None:
        console = Console()

        if not self.errors:
            console.print(f"[green]✔ No compile errors found in [bold]{self.name}[/]!")
            return

        table = Table(title=f"Compile Report for: {self.name}", show_lines=True)
        table.add_column("Code", style="red", no_wrap=True)
        table.add_column("Location", style="bold cyan")
        table.add_column("Message")

        for error in self.errors:
            table.add_row(error.code, error.location, error.message)

        console.print(table)
