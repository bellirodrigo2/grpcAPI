from typing import List, Optional, Protocol

from grpcAPI.makeproto.interface import IService
from grpcAPI.process_service import IncludeExclude, ProcessFilteredService


class AddComment(ProcessFilteredService):
    def __init__(
        self,
        comment: str,
        package: Optional[IncludeExclude] = None,
        module: Optional[IncludeExclude] = None,
        tags: Optional[IncludeExclude] = None,
        rule_logic: str = "and",  # "and", "or" or "hierarchical"
    ) -> None:
        super().__init__(
            package=package,
            module=module,
            tags=tags,
            rule_logic=rule_logic,
            true_service_cb=self._add_comment,
        )
        self.comment = comment.strip()

    def _add_comment(self, service: IService) -> None:
        if self.comment not in service.module_level_options:
            service.module_level_options.insert(0, self.comment)


class MakeOptions(Protocol):
    def __call__(
        self, package: Optional[str] = None, module: Optional[str] = None
    ) -> str: ...


class AddOptions(ProcessFilteredService):
    def __init__(
        self,
        options: List[MakeOptions],
        package: Optional[IncludeExclude] = None,
        module: Optional[IncludeExclude] = None,
        tags: Optional[IncludeExclude] = None,
        rule_logic: str = "and",  # "and", "or" or "hierarchical"
    ) -> None:
        super().__init__(
            package=package,
            module=module,
            tags=tags,
            rule_logic=rule_logic,
            true_service_cb=self._add_options,
        )
        self.options = options

    def _add_options(self, service: IService) -> None:
        mod_level_options = service.module_level_options

        for makeoption in self.options:
            try:
                option = makeoption(service.package, service.module).strip()
                if option and option not in mod_level_options:
                    mod_level_options.append(option)
            except Exception as _:
                pass
