from typing import Any, Dict, List, Optional

from grpcAPI.app import APIService, App
from grpcAPI.commands.command import GRPCAPICommand


class ListCommand(GRPCAPICommand):

    def __init__(self, app: App, settings_path: Optional[str] = None) -> None:
        super().__init__("list", app, settings_path, is_sync=True)

    def run_sync(self, **kwargs: Any) -> None:
        """List all active services with hierarchical tree display"""
        from collections import defaultdict

        from rich.console import Console
        from rich.tree import Tree

        console = Console()
        show_descriptions = kwargs.get("show_descriptions", False)

        services = list(self.app.service_list)

        if not services:
            console.print("[yellow]No services registered[/yellow]")
            return

        grouped: Dict[str, Dict[str, List[APIService]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for service in services:
            package = service.package or "(default)"
            module = service.module or "(default)"
            grouped[package][module].append(service)

        tree = Tree("[bold cyan]gRPC Services")

        total_services = 0
        total_methods = 0

        for package_name, modules in grouped.items():
            package_branch = tree.add(
                f"[Package] [bold blue]{package_name}[/bold blue]"
            )

            for module_name, services in modules.items():
                module_branch = package_branch.add(
                    f"[Module] [blue]{module_name}[/blue]"
                )

                for service in services:
                    total_services += 1

                    # Service name with description if available
                    service_text = f"[Service] [white]{service.name}[/white]"
                    if show_descriptions:
                        desc = service.description or service.comments or ""
                        if desc and desc.strip():
                            service_text += f" [dim]- {desc.strip()}[/dim]"

                    service_branch = module_branch.add(service_text)

                    # Add methods
                    for method in service.methods:
                        total_methods += 1
                        method_type = (method.is_server_stream, method.is_client_stream)
                        if method_type == (True, False):
                            method_icon = "[ServerStream]"  # streaming
                        elif method_type == (False, True):
                            method_icon = "[ClientStream]"  # client stream
                        elif method_type == (True, True):
                            method_icon = "[BiStream]"
                        else:
                            method_icon = "[RPC]"  # unary

                        method_text = f"{method_icon} [green]{method.name}[/green]"

                        if show_descriptions:
                            # Try to get method description from various sources
                            method_desc = ""
                            if hasattr(method, "description") and method.description:
                                method_desc = method.description.strip()
                            elif hasattr(method, "comment") and method.comment:
                                method_desc = method.comment.strip()
                            elif (
                                hasattr(method, "func")
                                and method.func
                                and method.func.__doc__
                            ):
                                method_desc = method.func.__doc__.strip()

                            if method_desc:
                                method_text += f" [dim]- {method_desc}[/dim]"

                        service_branch.add(method_text)

        console.print(tree)
        console.print(
            f"\n[dim]Total: {total_services} service(s) with {total_methods} method(s) in {len(grouped)} package(s)[/dim]"
        )
