from fnmatch import fnmatch
from typing import Any, Callable, Iterable, Optional, Union

from grpcAPI.makeproto import IService
from grpcAPI.makeproto.interface import IFilter, ILabeledMethod, IService


class ProcessService:
    def __init__(self, **kwargs: Any) -> None:
        pass

    def _process_service(self, service: IService) -> None:
        pass

    def _process_method(self, method: ILabeledMethod) -> None:
        pass

    def process(self, service: IService) -> None:
        self._process_service(service)
        for method in service.methods:
            self._process_method(method)


class IncludeExclude:
    def __init__(
        self,
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
    ) -> None:
        self.include = include or []
        self.exclude = exclude or []

    def should_include(self, name: Union[str, Iterable[str]]) -> bool:

        names = [name] if isinstance(name, str) else name

        def fnmatch_any(names: Iterable[str], patterns: Iterable[str]) -> bool:
            return any(fnmatch(n, p) for n in names for p in patterns)

        if self.include and not any(fnmatch_any(names, p) for p in self.include):
            return False
        if self.exclude and any(fnmatch_any(names, p) for p in self.exclude):
            return False
        return True

        # if self.exclude and any(fnmatch(name, p) for p in self.exclude):
        #     return False
        # return not self.include or any(fnmatch(name, p) for p in self.include)


class ProcessFilteredService(ProcessService):
    def __init__(
        self,
        true_service_cb: Optional[Callable[[IService], None]] = None,
        false_service_cb: Optional[Callable[[IService], None]] = None,
        true_method_cb: Optional[Callable[[ILabeledMethod], None]] = None,
        false_method_cb: Optional[Callable[[ILabeledMethod], None]] = None,
        package: Optional[IncludeExclude] = None,
        module: Optional[IncludeExclude] = None,
        tags: Optional[IncludeExclude] = None,
        rule_logic: str = "and",  # "and", "or" or "hierarchical"
    ) -> None:
        self.true_service_cb = true_service_cb
        self.false_service_cb = false_service_cb
        self.true_method_cb = true_method_cb
        self.false_method_cb = false_method_cb

        self.package_rules = package or IncludeExclude()
        self.module_rules = module or IncludeExclude()
        self.tags = tags or IncludeExclude()
        self.rule_logic = rule_logic

    def _should_include(self, service: IFilter) -> bool:
        results = [
            self.package_rules.should_include(service.package),
            self.module_rules.should_include(service.module),
            self.tags.should_include(service.tags),
        ]

        if self.rule_logic == "and":
            return all(results)
        elif self.rule_logic == "or":
            return any(results)
        elif not results[0]:
            return False
        elif not results[1]:
            return False
        else:
            return results[2]

    def _process_service(self, service: IService) -> None:
        if not self._should_include(service):
            if self.false_service_cb is not None:
                self.false_service_cb(service)
            return
        if self.true_service_cb is not None:
            self.true_service_cb(service)

    def _process_method(self, method: ILabeledMethod) -> None:
        if not self._should_include(method):
            if self.false_method_cb is not None:
                self.false_method_cb(method)
            return
        if self.true_method_cb is not None:
            self.true_method_cb(method)
