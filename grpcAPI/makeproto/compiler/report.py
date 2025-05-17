from dataclasses import dataclass
from typing import List, Optional

from rich.console import Console
from rich.table import Table


@dataclass
class CompileError:
    location: str
    message: str
    code: str


class CompileReport:
    def __init__(self, name: str, errors: Optional[List[CompileError]] = None) -> None:
        self.name = name
        self.errors: List[CompileError] = errors or []

    def __len__(self) -> int:
        return len(self.errors)

    def add_error(self, location: str, message: str, code: str = "E000") -> None:
        self.errors.append(CompileError(location, message, code))

    def is_valid(self) -> bool:
        return not self.errors

    def show(self) -> None:
        console = Console()
        table = Table(title=f"Compile Report for: {self.name}", show_lines=True)

        table.add_column("Code", style="red", no_wrap=True)
        table.add_column("Location", style="bold")
        table.add_column("Message")

        for error in self.errors:
            table.add_row(error.code, error.location, error.message)

        if not self.errors:
            console.print("[green]No compile errors found!")
        else:
            console.print(table)
