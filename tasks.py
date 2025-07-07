import shutil
from pathlib import Path

from invoke import task


@task
def install(c) -> None:
    c.run("pip install .")


@task
def install_dev(c) -> None:
    c.run("pip install .[dev]")


@task
def test(c) -> None:
    c.run("pytest -s")


@task
def lint(c) -> None:
    c.run("ruff check .")


@task
def format(c) -> None:
    c.run("black .")
    c.run("isort .")


@task
def build(c) -> None:
    c.run("python -m build")


@task
def clean(c) -> None:
    for path in ["dist", "build"]:
        p = Path(path)
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
    for egg_info in Path(".").glob("*.egg-info"):
        if egg_info.is_dir():
            shutil.rmtree(egg_info)
