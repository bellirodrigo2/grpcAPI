from typing import Any, Dict, List, Optional

from grpcAPI.app import APIService, App
from grpcAPI.commands.command import GRPCAPICommand


class ListCommand(GRPCAPICommand):

    def __init__(self, app: App, settings_path: Optional[str] = None) -> None:
        super().__init__("list", app, settings_path, is_sync=True)

    def _group_services(
        self, services: List[APIService]
    ) -> Dict[str, Dict[str, List[APIService]]]:
        """Group services by package and module."""
        from collections import defaultdict

        grouped: Dict[str, Dict[str, List[APIService]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for service in services:
            package = service.package or "(default)"
            module = service.module or "(default)"
            grouped[package][module].append(service)
        return grouped

    def _get_method_icon(self, method) -> str:
        """Get method type icon based on streaming characteristics."""
        method_type = (method.is_server_stream, method.is_client_stream)
        if method_type == (True, False):
            return "[ServerStream]"
        elif method_type == (False, True):
            return "[ClientStream]"
        elif method_type == (True, True):
            return "[BiStream]"
        else:
            return "[RPC]"

    def _get_method_description(self, method) -> str:
        """Extract method description from various sources."""
        if hasattr(method, "description") and method.description:
            return method.description.strip()
        elif hasattr(method, "comment") and method.comment:
            return method.comment.strip()
        elif hasattr(method, "func") and method.func and method.func.__doc__:
            return method.func.__doc__.strip()
        return ""

    def _build_service_tree(
        self, grouped: Dict[str, Dict[str, List[APIService]]], show_descriptions: bool
    ):
        """Build the service tree display and return tree, total_services, total_methods."""
        from rich.tree import Tree

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
                    service_text = f"[Service] [white]{service.name}[/white]"
                    if show_descriptions:
                        desc = service.description or service.comments or ""
                        if desc and desc.strip():
                            service_text += f" [dim]- {desc.strip()}[/dim]"

                    service_branch = module_branch.add(service_text)

                    for method in service.methods:
                        total_methods += 1
                        method_icon = self._get_method_icon(method)
                        method_text = f"{method_icon} [green]{method.name}[/green]"

                        if show_descriptions:
                            method_desc = self._get_method_description(method)
                            if method_desc:
                                method_text += f" [dim]- {method_desc}[/dim]"

                        service_branch.add(method_text)

        return tree, total_services, total_methods

    def run_sync(self, **kwargs: Any) -> None:
        """List all active services with hierarchical tree display"""
        from rich.console import Console

        console = Console()
        show_descriptions = kwargs.get("show_descriptions", False)
        services = list(self.app.service_list)

        if not services:
            console.print("[yellow]No services registered[/yellow]")
            return

        grouped = self._group_services(services)
        tree, total_services, total_methods = self._build_service_tree(
            grouped, show_descriptions
        )

        console.print(tree)
        console.print(
            f"\n[dim]Total: {total_services} service(s) with {total_methods} method(s) in {len(grouped)} package(s)[/dim]"
        )
