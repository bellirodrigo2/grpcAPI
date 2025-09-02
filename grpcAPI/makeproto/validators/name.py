import re
import tempfile
from pathlib import Path
from typing import List, Tuple

from typing_extensions import Optional, Sequence, Set

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate

VALID_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


PROTOBUF_RESERVED_WORDS = {
    "syntax",
    "import",
    "option",
    "package",
    "message",
    "enum",
    # "service",
    "rpc",
    "returns",
    "reserved",
    "repeated",
    "optional",
    "required",
    "map",
    "oneof",
    "extensions",
    "extend",
    "group",
    "true",
    "false",
}


def check_valid(name: str, report: CompileReport, check_reserveds: bool = True) -> None:

    if not name:
        report.report_error(
            code=CompileErrorCode.INVALID_NAME,
            location=name,
            override_msg=f"Invalid (Empty) name: '{name}'",
        )
    elif not VALID_NAME_RE.match(name):
        report.report_error(
            code=CompileErrorCode.INVALID_NAME,
            location=name,
            override_msg=f"Invalid name: '{name}'",
        )
    elif check_reserveds and name in PROTOBUF_RESERVED_WORDS:
        report.report_error(
            code=CompileErrorCode.RESERVED_NAME,
            location=name,
            override_msg=f"Protobuf reserved name: '{name}'",
        )


class NameValidator(CompilerPass):
    def __init__(
        self,
        used_names: Optional[Set[str]] = None,
    ) -> None:
        super().__init__()
        self.used_names = used_names or set()

    def _check_already_used(self, msg: str, name: str, report: CompileReport) -> None:
        if name in self.used_names:
            report.report_error(
                code=CompileErrorCode.DUPLICATED_NAME,
                location=name,
                override_msg=msg,
            )
        else:
            self.used_names.add(name)


class BlockNameValidator(NameValidator):

    def visit_service(self, block: ServiceTemplate) -> None:
        name = block.name
        report = self.ctx.get_report(block)
        check_valid(name, report)
        self._check_already_used(
            f"Duplicated Service name '{name}' in the package",
            block.name,
            report,
        )


class FieldNameValidator(NameValidator):
    def reset(self) -> None:
        self.used_names.clear()

    def visit_service(self, block: ServiceTemplate) -> None:
        for field in block.methods:
            field.accept(self)

    def visit_method(self, method: MethodTemplate) -> None:
        name = method.name
        report = self.ctx.get_report(method.service)
        check_valid(name, report)
        self._check_already_used(
            method.name,
            f"Duplicated Method name '{name}' in the service '{method.service.name}'",
            report,
        )


def check_valid_filenames(names: Sequence[str], report: CompileReport) -> None:

    fail_names = find_invalid_filenames(names)

    for name, err in fail_names:
        report.report_error(
            code=CompileErrorCode.INVALID_NAME,
            location=name,
            override_msg=f'Invalid File Name Error for {name}:\n "{err}"',
        )


def find_invalid_filenames(filenames: Sequence[str]) -> Sequence[Tuple[str, str]]:
    errors: List[Tuple[str, str]] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for name in filenames:
            try:
                file_path = tmp_path / name
                file_path.write_text("test")
            except (OSError, ValueError, TypeError) as e:
                errors.append((name, str(e)))
    return errors
