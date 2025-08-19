from example.guber.server.app import app
from grpcAPI.commands.list import ListCommand


def test_list() -> None:

    listcmd = ListCommand(
        app,
    )

    listcmd.run_sync()
