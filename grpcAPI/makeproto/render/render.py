from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Set

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
env = Environment(
    trim_blocks=True,  # remove a newline after a block
    lstrip_blocks=True,  # remove leading spaces before a block
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
)

macros = env.get_template("macros.j2")
render_block = macros.module.render_block
protofile_template = env.get_template("protofile.j2")
render_protofile = protofile_template.render


@dataclass
class BaseModuleTemplate:
    modulename: str
    version: int
    package: str
    imports: Set[str]
    description: str
    options: List[str]
    fields: List[str]

    def add_field(self, field: Dict[str, Any]) -> None:
        field_str = self.render_block(field)
        self.fields.append(field_str)

    def render(self) -> str:
        return self.render_protofile(asdict(self))

    @property
    def render_block(self) -> Callable[[Dict[str, Any]], str]:
        return render_block

    @property
    def render_protofile(Self) -> Callable[[Dict[str, Any]], str]:
        return render_protofile
