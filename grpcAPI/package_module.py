from dataclasses import dataclass
from typing import List, Optional, Sequence

from grpcAPI.app import APIService


@dataclass
class MetaData:
    name: str
    options: Sequence[str]
    comments: Sequence[str]


@dataclass
class APIModule(MetaData):
    package: str

    def make_service(
        self,
        service_name: str,
        options: Optional[List[str]] = None,
        comments: str = "",
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> APIService:
        return APIService(
            name=service_name,
            module=self.name,
            package=self.package,
            module_level_options=self.options,
            module_level_comments=self.comments,
            title=title,
            description=description,
            tags=tags,
            options=options,
            comments=comments,
        )


@dataclass
class APIPackage(MetaData):

    def make_module(
        self,
        module_name: str,
    ) -> APIModule:
        return APIModule(
            name=module_name,
            package=self.name,
            comments=self.comments,
            options=self.options,
        )
