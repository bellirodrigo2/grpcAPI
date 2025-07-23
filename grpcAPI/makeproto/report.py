from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from rich.console import Console
from rich.table import Table


class CompileErrorCode(Enum):
    # E100 - Names
    INVALID_NAME = ("E101", "Invalid name", "Name does not match the expected pattern")
    RESERVED_NAME = ("E102", "Reserved name", "Name is a reserved Protobuf keyword")
    DUPLICATED_NAME = (
        "E104",
        "Duplicated name",
        "Name is used more than once in the same block",
    )

    # E200 - Imports
    INVALID_CLASS_PROTO_PATH = (
        "E201",
        "Invalid class",
        "Class 'proto_path' attribute is not defined",
    )

    # E400 - Descrições
    INVALID_COMMENT = (
        "E401",
        "Invalid comment",
        "Comment must be a string",
    )

    # E500 - Opções
    INVALID_OPTIONS = (
        "E501",
        "Invalid options",
        "Options must be a List[str]",
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
    METHOD_NOT_CONSISTENT_TO_RETURN = (
        "E805",
        "Invalid Streaming mode return type",
        "Function return should be consistent with it´s return type (AsyncIterator)",
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
        "E901",
        "Setter Error",
        "Error during set step. This is a system error",
    )
    RUNTIME_POSSIBLE_ERROR = ("E902", "Possible runtime error", "")

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
        return f"{self.message}: {self.description}"  # pragma: no cover


@dataclass
class CompileError:
    code: str
    message: str
    location: str

    def __str__(self) -> str:
        return f"Compile Error <code={self.code}, message={self.message},location={self.location}>"  # pragma: no cover


class CompileReport:
    def __init__(self, name: str, errors: Optional[List[CompileError]] = None) -> None:
        self.name = name
        self.errors: List[CompileError] = errors or []

    def __len__(self) -> int:
        return len(self.errors)

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

    def is_valid(self) -> bool:
        return not self.errors  # pragma: no cover

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
