from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from rich.console import Console
from rich.table import Table

# ========== DEFINIÇÃO ESTÁTICA DE ERROS ==========


class CompileErrorCode(Enum):
    # E100 - Nomes
    INVALID_NAME = ("E101", "Invalid name", "Name does not match the expected pattern")
    RESERVED_NAME = ("E102", "Reserved name", "Name is a reserved Protobuf keyword")
    NAME_RESERVED_IN_BLOCK = (
        "E103",
        "Name reserved in block",
        "Field name is reserved within this block",
    )
    DUPLICATED_NAME = (
        "E104",
        "Duplicated name",
        "Name is used more than once in the same block",
    )

    # E200 - Índices
    INVALID_INDEX_TYPE = (
        "E201",
        "Invalid index type",
        "Field or reserved index must be an integer",
    )
    DUPLICATE_INDEX = ("E202", "Duplicate index", "Index is already used in the block")
    INDEX_OUT_OF_RANGE = (
        "E203",
        "Index out of range",
        "Index is outside the valid range",
    )
    RESERVED_INDEX = (
        "E204",
        "Index is reserved",
        "Reserved by block statement",
    )
    INVALID_ENUM_INDEX = (
        "E205",
        "Enum Block invalid index set",
        'Enum block should have a default "0" index',
    )

    # E300 - Estrutura dos blocos
    ENUM_MUST_HAVE_FIELDS = (
        "E301",
        "Invalid enum block",
        "Enum block must contain only fields",
    )
    ONEOF_MUST_HAVE_FIELDS = (
        "E302",
        "Invalid oneof block",
        "Oneof blocks must contain only fields",
    )
    UNLINKED_FIELD = (
        "E303",
        "Unlinked Field",
        "Every Field should be linked to a block",
    )

    # E400 - Descrições
    INVALID_DESCRIPTION = (
        "E401",
        "Invalid description",
        "Description must be a string",
    )
    # INVALID_BLOCK_DESCRIPTION = (
    #     "E411",
    #     "Invalid block description",
    #     "Description must be a string",
    # )
    # INVALID_FIELD_DESCRIPTION = (
    #     "E421",
    #     "Invalid field description",
    #     "Description must be a string",
    # )
    # INVALID_METHOD_DESCRIPTION = (
    #     "E431",
    #     "Invalid method description",
    #     "Description must be a string",
    # )

    # E500 - Opções
    INVALID_OPTIONS = (
        "E501",
        "Invalid options",
        "Options must be a dictionary",
    )
    INVALID_KEY_OPTIONS = (
        "E502",
        "Invalid options",
        "Option keys must be strings",
    )
    INVALID_VALUE_OPTIONS = (
        "E503",
        "Invalid options",
        "Option values must be string or boolean",
    )
    # INVALID_BLOCK_OPTIONS = (
    #     "E512",
    #     "Invalid block options",
    #     "Options must be a dictionary",
    # )
    # INVALID_BLOCK_OPTION_KEY = (
    #     "E513",
    #     "Invalid option key",
    #     "Option keys must be strings",
    # )
    # INVALID_BLOCK_OPTION_VALUE = (
    #     "E514",
    #     "Invalid option value",
    #     "Option values must be string or boolean",
    # )
    # INVALID_FIELD_OPTIONS = (
    #     "E522",
    #     "Invalid field options",
    #     "Options must be a dictionary",
    # )
    # INVALID_FIELD_OPTION_KEY = (
    #     "E523",
    #     "Invalid field option key",
    #     "Option keys must be strings",
    # )
    # INVALID_FIELD_OPTION_VALUE = (
    #     "E524",
    #     "Invalid field option value",
    #     "Option values must be string or boolean",
    # )
    # INVALID_METHOD_OPTIONS = (
    #     "E532",
    #     "Invalid method options",
    #     "Options must be a dictionary",
    # )
    # INVALID_METHOD_OPTION_KEY = (
    #     "E533",
    #     "Invalid method option key",
    #     "Option keys must be strings",
    # )
    # INVALID_METHOD_OPTION_VALUE = (
    #     "E534",
    #     "Invalid method option value",
    #     "Option values must be string or boolean",
    # )

    FIELD_TYPE_INVALID = (
        "E621",
        "Invalid field type",
        "Type is not supported or not recognized",
    )

    # E800 - Métodos
    METHOD_INVALID_REQUEST_TYPE = (
        "E801",
        "Invalid request type",
        "Request type is invalid or not a BaseMessage",
    )
    METHOD_INVALID_RESPONSE_TYPE = (
        "E804",
        "Invalid response type",
        "Response type is invalid or not a BaseMessage",
    )
    METHOD_RETURN_STREAM_IS_NOT_ASYNC_GENERATOR = (
        "E805",
        "Stream return invalid",
        "Return stream must be an async generator",
    )
    METHOD_INVALID_DESCRIPTION_TYPE = (
        "E806",
        "Invalid description type",
        "Description must be a string",
    )
    METHOD_OPTIONS_NOT_DICT = (
        "E807",
        "Options must be a dict",
        "Method options must be a dictionary",
    )
    METHOD_OPTION_KEY_NOT_STRING = (
        "E808",
        "Option key not string",
        "Option keys must be strings",
    )
    METHOD_OPTION_VALUE_INVALID = (
        "E809",
        "Invalid option value",
        "Option value must be a string or boolean",
    )

    # E999 - Outros
    SETTER_PASS_ERROR = (
        "E999",
        "Setter Error",
        "Error during set step. This is a system error",
    )

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]

    @property
    def description(self) -> str:
        return self.value[2]

    @property
    def full_message(self) -> str:
        return f"{self.message}: {self.description}"


# ========== INSTÂNCIA DE ERRO OCORRIDO ==========


@dataclass
class CompileError:
    code: str
    message: str
    location: str

    def __str__(self) -> str:
        return f"Compile Error <code={self.code}, message={self.message},location={self.location}>"


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
        description = override_msg or code.description
        message = f"{code.message}: {description}"
        self.errors.append(
            CompileError(code=code.code, message=message, location=location)
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

    def __repr__(self) -> str:
        return f"CompileReport(name='{self.name}', errors={self.errors})"
