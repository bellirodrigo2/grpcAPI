from pytest import CaptureFixture

from example.guber.server.app import app
from grpcAPI.commands.list import ListCommand


def test_list(capsys: CaptureFixture[str]) -> None:

    listcmd = ListCommand(
        app,
    )

    listcmd.run_sync()
    captured = capsys.readouterr()

    assert "gRPC Services" in captured.out
