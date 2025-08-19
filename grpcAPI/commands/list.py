from collections import defaultdict
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from grpcAPI.app import APIService, App
from grpcAPI.commands.command import GRPCAPICommand
from grpcAPI.makeproto.interface import ILabeledMethod


def display_services_list(services: List[APIService]) -> None:
    """Display a formatted list of services and their methods using rich tables"""
    console = Console()

    if not services:
        console.print("[yellow]No services found[/]")
        return

    grouped: Dict[str, Dict[str, List[APIService]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for service in services:
        package = service.package or "(default)"
        module = service.module or "(default)"
        grouped[package][module].append(service)

    for package_name, modules in grouped.items():
        console.rule(f"[bold blue]Package: {package_name}")

        for module_name, module_services in modules.items():

            table = Table(
                title=f"Module: {module_name}",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            table.add_column("Service", style="green", no_wrap=True)
            table.add_column("Methods", style="cyan")
            table.add_column("Description", style="dim")

            for service in module_services:
                method_info = []
                for method in service.methods:
                    method_descriptor = _get_method_descriptor(method)
                    method_info.append(f"{method.name} {method_descriptor}")

                methods_text = "\n".join(method_info) if method_info else "No methods"

                description = (
                    service.description or service.comments or "No description"
                )
                if service.description and service.description.strip():
                    description = service.description.strip()
                elif service.comments and service.comments.strip():
                    description = service.comments.strip()
                else:
                    description = "No description"

                table.add_row(service.name, methods_text, description)

            console.print(table)
            console.print()


def _get_method_descriptor(method: ILabeledMethod) -> str:
    if method.description and method.description.strip():
        return method.description.strip()

    request_types = (
        ", ".join([t.argtype.__name__ for t in method.request_types])
        if method.request_types
        else "Empty"
    )
    response_type = (
        method.response_types.argtype.__name__ if method.response_types else "Empty"
    )

    # Determine if it's streaming
    is_streaming = (
        any("stream" in opt.lower() for opt in method.options)
        if method.options
        else False
    )
    streaming_indicator = "streaming" if is_streaming else "unary"

    return f"({request_types}) -> {response_type} [{streaming_indicator}]"


class ListCommand(GRPCAPICommand):

    def __init__(self, app: App, settings_path: Optional[str] = None) -> None:
        super().__init__("list", app, settings_path, is_sync=True)

    def run_sync(self, **kwargs: Any) -> None:
        """List all active services with summarized info about services and methods"""
        display_services_list(self.app.services)
