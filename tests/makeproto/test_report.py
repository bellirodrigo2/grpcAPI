import pytest

from grpcAPI.makeproto.compiler import CompilerContext
from grpcAPI.makeproto.report import CompileError, CompileErrorCode, CompileReport


def test_show_no_errors(capfd: pytest.CaptureFixture[str]) -> None:
    report = CompileReport("TestModule", errors=[])

    report.show()

    out, err = capfd.readouterr()
    assert "No compile errors found" in out
    assert "TestModule" in out


def test_show_with_errors(capfd: pytest.CaptureFixture[str]) -> None:
    errors = [
        CompileError("E001", "line 10", "Syntax error"),
        CompileError("E002", "line 20", "Name not defined"),
    ]
    report = CompileReport("MyModule", errors)

    report.show()

    out, err = capfd.readouterr()
    assert "Compile Report for: MyModule" in out
    assert "E001" in out
    assert "line 10" in out
    assert "Syntax error" in out
    assert "E002" in out
    assert "line 20" in out
    assert "Name not defined" in out

    assert str(report).startswith("CompileReport(name=")


def test_show_ctx_with_errors(capfd: pytest.CaptureFixture[str]) -> None:

    ctx = CompilerContext("Test", {})

    class Mock:
        def __init__(self, name: str) -> None:
            self.name = name

    report = ctx.get_report(Mock("mock"))
    ctx.show()

    report.report_error(CompileErrorCode.DUPLICATED_NAME, "test")

    ctx.show()

    out, err = capfd.readouterr()
    assert "Compile Report for: mock" in out
    assert "E104" in out
    assert "test" in out
    assert "Duplicated name:" in out
    assert str(report).startswith("CompileReport(name=")
