from example.guber.server.app import app
from grpcAPI.commands.lint import LintCommand


def test_lint() -> None:

    lint = LintCommand(
        app,
    )
    proto_packages = lint.run_sync()
    packages = [(pack.package, pack.filename) for pack in proto_packages]
    assert ("account", "service") in packages
    assert ("ride", "user") in packages
    assert ("ride", "driver") in packages
    assert ("ride", "ride") in packages
