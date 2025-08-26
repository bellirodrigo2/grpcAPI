#!/usr/bin/env python3
import asyncio
import logging  # noqa: F401
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from grpcAPI.commands.settings.utils import load_app
from grpcAPI.logger import LOGGING_CONFIG

# Try to import version, fallback to default
try:
    from grpcAPI import __version__
except ImportError:
    __version__ = "0.1.0"
from grpcAPI.app import GrpcAPI
from grpcAPI.commands.build import BuildCommand
from grpcAPI.commands.init import InitCommand
from grpcAPI.commands.lint import LintCommand
from grpcAPI.commands.list import ListCommand
from grpcAPI.commands.run import RunCommand

# Initialize Rich console
console = Console()


def setup_cli_logging(verbose: bool = False):
    """Setup logging for CLI operations using the unified LOGGING_CONFIG"""
    import logging.config

    # Clone the config so we don't modify the original
    cli_config = LOGGING_CONFIG.copy()

    # Update grpcAPI logger level based on verbose flag
    if "loggers" in cli_config:
        if "grpcAPI" in cli_config["loggers"]:
            cli_config["loggers"]["grpcAPI"]["level"] = "INFO" if verbose else "INFO"

        # Ensure server_logger_plugin is configured
        cli_config["loggers"]["server_logger_plugin"] = {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }

    # Reconfigure logging with our CLI-optimized settings
    logging.config.dictConfig(cli_config)


def get_app_instance(app_path: str) -> GrpcAPI:
    load_app(app_path)
    return GrpcAPI()


def print_banner():
    banner = """
    TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW
    Q          gRPC API Framework          Q
    Q     Protocol Buffer Magic (         Q
    ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]
    """
    console.print(Panel(Text(banner, style="bold cyan"), style="blue", expand=False))


def handle_error(e: Exception, command: str):
    """Handle errors with rich formatting and detailed information"""
    import traceback

    console.print(f"\nError in {command} command:", style="bold red")
    console.print(f"[red]{type(e).__name__}: {str(e)}[/red]")

    # Show traceback for better debugging
    console.print("\n[dim]Traceback (most recent call last):[/dim]")
    tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
    for line in tb_lines[-5:]:  # Show last 5 lines of traceback
        console.print(f"[dim]{line.strip()}[/dim]")

    console.print("\n[yellow]Try running with --help for more information[/yellow]")
    console.print(
        "[dim]If this error persists, check your file paths and configuration.[/dim]"
    )
    sys.exit(1)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx, version):
    """
    =� gRPC API Framework CLI

    A modern toolkit for building gRPC services with automatic
    protocol buffer generation, dependency injection, and more.
    """
    if version:
        console.print(
            f"[bold cyan]gRPC API Framework[/bold cyan] version [bold green]{__version__}[/bold green]"
        )
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("Type [bold]grpcapi --help[/bold] for available commands.\n")


@cli.command()
@click.argument("app_path", type=str)
@click.option("--host", "-h", help="Server host address")
@click.option("--port", "-p", help="Server port")
@click.option("--settings", "-s", help="Path to settings file")
@click.option("--no-lint", is_flag=True, help="Skip protocol buffer validation")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def run(
    app_path: str,
    host: Optional[str],
    port: Optional[int],
    settings: Optional[str],
    no_lint: bool,
    verbose: bool,
):
    """
    <� Run the gRPC server

    Starts your gRPC server with automatic protocol buffer generation,
    service registration, and optional plugins like health checking
    and reflection.
    """
    try:
        # Setup logging for the CLI
        setup_cli_logging(verbose)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("=� Starting gRPC server...", total=None)

            app = get_app_instance(app_path)
            command = RunCommand(app, settings)

            console.print(
                f"[bold green] Server starting on {host}:{port}[/bold green]"
            )
            console.print(f"[dim]Settings: {settings or 'default'}[/dim]")
            console.print(f"[dim]Lint: {'disabled' if no_lint else 'enabled'}[/dim]\n")

        asyncio.run(command.run(host=host, port=port, lint=not no_lint))

    except Exception as e:
        handle_error(e, "run")


@cli.command()
@click.argument("app_path", type=str)
@click.option("--output", "-o", help="Output directory for proto files")
@click.option("--settings", "-s", help="Path to settings file")
@click.option("--overwrite", is_flag=True, help="Overwrite existing files")
@click.option("--zip", is_flag=True, help="Create zip archive of generated files")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def build(
    app_path: str,
    output: str,
    settings: Optional[str],
    overwrite: bool,
    zip: bool,
    verbose: bool,
):
    """
    =( Build protocol buffer files

    Generates .proto files from your service definitions with validation,
    formatting, and optional compression. Perfect for distribution or
    external consumption.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("=( Building protocol buffers...", total=None)

            app = get_app_instance(app_path)
            command = BuildCommand(app, settings)

            result = command.execute(
                outdir=output,
                overwrite=overwrite,
                zipcompress=zip,
            )

            progress.remove_task(task)

        # Display results
        table = Table(title="=� Build Results")
        table.add_column("File", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")

        if isinstance(result, set):
            for file in result:
                table.add_row(str(file), " Generated")

        console.print("\n")
        console.print(table)
        console.print(f"\n[bold green] Build completed! Output: {output}[/bold green]")

    except Exception as e:
        handle_error(e, "build")


@cli.command()
@click.argument("app_path", type=str)
@click.option("--settings", "-s", help="Path to settings file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation info")
def lint(app_path: str, settings: Optional[str], verbose: bool):
    """
    🔍 Validate service definitions

    Performs comprehensive validation of your gRPC services including
    type checking, naming conventions, and protocol buffer compatibility
    without generating files.
    """
    try:
        # Setup logging for CLI operations
        setup_cli_logging(verbose)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("🔍 Validating services...", total=None)

            app = get_app_instance(app_path)
            command = LintCommand(app, settings)
            proto_files = command.execute()

        # Display validation results
        console.print("\n[bold green] Validation successful![/bold green]\n")

        if verbose and proto_files:
            table = Table(title="=� Service Validation Details")
            table.add_column("Package", style="cyan")
            table.add_column("File", style="white")
            table.add_column("Status", style="green")

            for proto in proto_files:
                table.add_row(proto.package, proto.filename, " Valid")

            console.print(table)

        count = len(list(proto_files)) if proto_files else 0
        console.print(f"[dim]Validated {count} protocol buffer file(s)[/dim]")

    except Exception as e:
        handle_error(e, "lint")


@cli.command("list")
@click.argument("app_path", type=str)
@click.option("--settings", "-s", help="Path to settings file")
@click.option(
    "--show-descriptions", is_flag=True, help="Show service and method descriptions"
)
def list_services(app_path: str, settings: Optional[str], show_descriptions: bool):
    """
    List registered services

    Shows all registered gRPC services in a hierarchical tree format:
    package > module > service > method with optional descriptions.
    """
    try:
        app = get_app_instance(app_path)
        command = ListCommand(app, settings)
        command.execute(show_descriptions=show_descriptions)

    except Exception as e:
        handle_error(e, "list")


@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing config file")
@click.option("--output", "-o", help="Output directory (defaults to current directory)")
def init(force: bool, output: Optional[str]):
    """
    🆕 Initialize gRPC API configuration

    Creates a grpcapi.config.json file in the current directory with
    default settings for protocol buffer generation, server configuration,
    and plugin settings.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("🆕 Creating configuration...", total=None)

            command = InitCommand(settings_path=None)
            command.execute(force=force, dst=Path(output) if output else Path.cwd())

        config_path = (Path(output) if output else Path.cwd()) / "grpcapi.config.json"

        console.print(
            f"\n[bold green] Project '{config_path.stem}' created successfully![/bold green]"
        )
        console.print(f"[dim]Config file: {config_path}[/dim]\n")

        # Show next steps
        steps = Panel(
            "[bold]Next Steps:[/bold]\n\n"
            f"1. [cyan]Edit {config_path.name}[/cyan] to customize settings\n"
            "2. [cyan]Create your app.py with services[/cyan]\n"
            "3. [cyan]grpcapi run app.py[/cyan]\n\n"
            "[dim]=� Use 'grpcapi --help' for more commands[/dim]",
            title="=� Get Started",
            style="green",
        )
        console.print(steps)

    except Exception as e:
        handle_error(e, "init")


@cli.command()
def version():
    """Show version information"""
    info_table = Table.grid(padding=1)
    info_table.add_column(style="cyan", no_wrap=True)
    info_table.add_column()

    info_table.add_row("Version:", f"[bold]{__version__}[/bold]")
    info_table.add_row("Python:", f"{sys.version.split()[0]}")

    console.print("\n[bold cyan]gRPC API Framework[/bold cyan]")
    console.print(info_table)
    console.print()


def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
