from typing import Any, Dict, Iterable

from grpcAPI.process_service import IncludeExclude, ProcessFilteredService


class DisableService(ProcessFilteredService):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:

        if "service_filter" not in kwargs:
            super().__init__()
        else:
            empty_kwargs: Dict[str, Iterable[str]] = {
                "include": [],
                "exclude": [],
            }
            fitler_kwargs = kwargs["service_filter"]
            package = fitler_kwargs.get("package", empty_kwargs)
            module = fitler_kwargs.get("module", empty_kwargs)
            tags = fitler_kwargs.get("tags", empty_kwargs)
            rule_logic = fitler_kwargs.get("rule_logic", "and")
            super().__init__(
                package=IncludeExclude(**package),
                module=IncludeExclude(**module),
                tags=IncludeExclude(**tags),
                rule_logic=rule_logic,
            )

    def _disable(self, block: Any) -> None:
        block._active = False
