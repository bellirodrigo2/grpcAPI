from typing_extensions import List

from grpcAPI.app import BaseService
from grpcAPI.extract_types import extract_request_response_type


class APIService(BaseService):

    def __init__(
        self,
        name: str,
        options: List[str] | None = None,
        comments: str = "",
        module: str = "service",
        package: str = "",
    ) -> None:
        super().__init__(
            extract_request_response_type, name, options, comments, module, package
        )
