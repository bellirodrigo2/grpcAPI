# tasks.py

from invoke import task


@task
def install(c):
    c.run("pip install .[dev]")


@task
def test(c):
    c.run("python -m unittest discover -s tests")


@task
def lint(c):
    c.run("ruff check .")


@task
def format(c):
    c.run("black .")
    c.run("isort .")


@task
def build(c):
    c.run("python -m build")


@task
def clean(c):
    c.run("rm -rf dist/ build/ *.egg-info")
