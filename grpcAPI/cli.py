#!/usr/bin/env python3
import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from grpcAPI import __version__ if hasattr(__import__('grpcAPI'), '__version__') else "0.1.0"
from grpcAPI.app import GrpcAPI
from grpcAPI.commands.build import BuildCommand
from grpcAPI.commands.init import InitCommand
from grpcAPI.commands.lint import LintCommand
from grpcAPI.commands.list import ListCommand
from grpcAPI.commands.run import RunCommand

# Initialize Rich console
console = Console()

# Global app instance for commands that need it
app_instance: Optional[GrpcAPI] = None


def get_app_instance() -> GrpcAPI:
    global app_instance
    if app_instance is None:
        app_instance = GrpcAPI()
    return app_instance


def print_banner():
    banner = """
    TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW
    Q          gRPC API Framework          Q
    Q     Protocol Buffer Magic (         Q
    ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]
    """
    console.print(Panel(
        Text(banner, style="bold cyan"),
        style="blue",
        expand=False
    ))


def handle_error(e: Exception, command: str):
    console.print(f"\nL [bold red]Error in {command} command:[/bold red]")
    console.print(f"[red]{str(e)}[/red]")
    console.print("\n=� [yellow]Try running with --help for more information[/yellow]")
    sys.exit(1)


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version and exit')
@click.pass_context
def cli(ctx, version):
    """
    =� gRPC API Framework CLI
    
    A modern toolkit for building gRPC services with automatic
    protocol buffer generation, dependency injection, and more.
    """
    if version:
        console.print(f"[bold cyan]gRPC API Framework[/bold cyan] version [bold green]{__version__}[/bold green]")
        sys.exit(0)
    
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("Type [bold]grpcapi --help[/bold] for available commands.\n")


@cli.command()
@click.option('--host', '-h', default='localhost', help='Server host address')
@click.option('--port', '-p', default=50051, help='Server port')
@click.option('--settings', '-s', help='Path to settings file')
@click.option('--no-lint', is_flag=True, help='Skip protocol buffer validation')
def run(host: str, port: int, settings: Optional[str], no_lint: bool):
    """
    <� Run the gRPC server
    
    Starts your gRPC server with automatic protocol buffer generation,
    service registration, and optional plugins like health checking
    and reflection.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("=� Starting gRPC server...", total=None)
            
            app = get_app_instance()
            command = RunCommand(app, settings)
            
            console.print(f"[bold green] Server starting on {host}:{port}[/bold green]")
            console.print(f"[dim]Settings: {settings or 'default'}[/dim]")
            console.print(f"[dim]Lint: {'disabled' if no_lint else 'enabled'}[/dim]\n")
            
            asyncio.run(command.run(host=host, port=port, lint=not no_lint))
            
    except Exception as e:
        handle_error(e, "run")


@cli.command()
@click.option('--output', '-o', default='./proto', help='Output directory for proto files')
@click.option('--settings', '-s', help='Path to settings file')
@click.option('--overwrite', is_flag=True, help='Overwrite existing files')
@click.option('--zip', is_flag=True, help='Create zip archive of generated files')
@click.option('--clean', is_flag=True, help='Clean unused service files')
def build(output: str, settings: Optional[str], overwrite: bool, zip: bool, clean: bool):
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
            
            app = get_app_instance()
            command = BuildCommand(app, settings)
            
            result = command.execute(
                output=output, 
                overwrite=overwrite, 
                zipcompress=zip,
                clean_services=clean
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
@click.option('--settings', '-s', help='Path to settings file')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation info')
def lint(settings: Optional[str], verbose: bool):
    """
    🔍 Validate service definitions
    
    Performs comprehensive validation of your gRPC services including
    type checking, naming conventions, and protocol buffer compatibility
    without generating files.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("🔍 Validating services...", total=None)
            
            app = get_app_instance()
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
                table.add_row(
                    proto.package, 
                    proto.filename,
                    " Valid"
                )
            
            console.print(table)
        
        count = len(list(proto_files)) if proto_files else 0
        console.print(f"[dim]Validated {count} protocol buffer file(s)[/dim]")
        
    except Exception as e:
        handle_error(e, "lint")


@cli.command('list')
@click.option('--settings', '-s', help='Path to settings file')
@click.option('--format', '-f', type=click.Choice(['table', 'tree']), default='table', help='Output format')
@click.option('--show-methods', is_flag=True, help='Show methods for each service')
def list_services(settings: Optional[str], format: str, show_methods: bool):
    """
    =� List registered services
    
    Shows all registered gRPC services with their methods, packages,
    and metadata. Great for debugging and documentation.
    """
    try:
        app = get_app_instance()
        command = ListCommand(app, settings)
        services_info = command.execute()
        
        if not services_info:
            console.print("[yellow]No services registered[/yellow]")
            return
        
        if format == 'tree':
            tree = Tree("<3 [bold cyan]gRPC Services")
            
            for package_name, services in services_info.items():
                package_branch = tree.add(f"=� {package_name}")
                
                for service in services:
                    service_branch = package_branch.add(f"=' {service.name}")
                    
                    if show_methods:
                        for method in service.methods:
                            method_type = "=" if method.is_server_stream else "=�"
                            service_branch.add(f"{method_type} {method.name}")
            
            console.print(tree)
        
        else:  # table format
            table = Table(title="=� Registered Services")
            table.add_column("Package", style="cyan", no_wrap=True)
            table.add_column("Service", style="white")
            table.add_column("Methods", style="green")
            table.add_column("Active", style="yellow")
            
            for package_name, services in services_info.items():
                for service in services:
                    method_count = len(service.methods)
                    active_status = "" if service.active else "L"
                    
                    methods_text = str(method_count)
                    if show_methods and service.methods:
                        method_names = [m.name for m in service.methods[:3]]
                        if len(service.methods) > 3:
                            method_names.append("...")
                        methods_text = f"{method_count} ({', '.join(method_names)})"
                    
                    table.add_row(
                        package_name,
                        service.name,
                        methods_text,
                        active_status
                    )
            
            console.print("\n")
            console.print(table)
        
        total_services = sum(len(services) for services in services_info.values())
        console.print(f"\n[dim]Total: {total_services} service(s) in {len(services_info)} package(s)[/dim]")
        
    except Exception as e:
        handle_error(e, "list")


@cli.command()
@click.argument('project_name')
@click.option('--template', '-t', default='basic', help='Project template to use')
@click.option('--output', '-o', help='Output directory (defaults to project name)')
def init(project_name: str, template: str, output: Optional[str]):
    """
    <� Initialize a new gRPC API project
    
    Creates a new project structure with example services, configuration,
    and development tools. Perfect for getting started quickly.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(f"<� Creating project '{project_name}'...", total=None)
            
            command = InitCommand(settings_path=None)
            result = command.execute(
                project_name=project_name,
                template=template,
                output=output or project_name
            )
            
        project_path = Path(output or project_name).absolute()
        
        console.print(f"\n[bold green] Project '{project_name}' created successfully![/bold green]")
        console.print(f"[dim]Location: {project_path}[/dim]\n")
        
        # Show next steps
        steps = Panel(
            "[bold]Next Steps:[/bold]\n\n"
            f"1. [cyan]cd {project_name}[/cyan]\n"
            "2. [cyan]pip install -e .[dev][/cyan]\n"
            "3. [cyan]grpcapi run[/cyan]\n\n"
            "[dim]=� Use 'grpcapi --help' for more commands[/dim]",
            title="=� Get Started",
            style="green"
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


if __name__ == '__main__':
    main()