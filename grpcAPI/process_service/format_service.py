from inflection import camelize
from inflection import underscore as snake_case
from makeproto import IService
from typing_extensions import Any, List, Literal, Mapping, Optional, Tuple

from grpcAPI.interfaces import Labeled, ProcessService


class FormatServiceFactory:
    def __call__(self, settings: Mapping[str, Any]) -> "FormatService":

        max_char, title_case, comment_strategy = get_format_settings(settings)
        max_char = max_char or 80
        title_case = title_case or "none"
        comment_strategy = comment_strategy or "multiline"

        return FormatService(max_char, title_case, comment_strategy)


def get_format_settings(
    settings: Mapping[str, Any],
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    format_settings = settings.get("format", {})
    max_char = format_settings.get("max_char_per_line", None)
    case = format_settings.get("case", None)
    comment_strategy = format_settings.get("comment_style", None)
    return max_char, case, comment_strategy


class FormatService(ProcessService):

    def __init__(
        self,
        max_char: int = 80,
        case: Literal["snake", "camel", "pascal", "none"] = "none",
        strategy: Literal["singleline", "multiline"] = "multiline",
    ) -> None:
        self.max_char = max_char
        self.case = case
        if "multi" in strategy:
            self.open_char = "/*\n"
            self.close_char = "*/\n"
            self.start_char = "*"
            self.end_char = "*"
            self.fill_char = "*"
        else:
            self.open_char = ""
            self.close_char = ""
            self.start_char = "//"
            self.end_char = ""
            self.fill_char = " "

    def __call__(self, service: IService) -> None:
        format_comment(
            service=service,
            max_char=self.max_char,
            open_char=self.open_char,
            close_char=self.close_char,
            start_char=self.start_char,
            end_char=self.end_char,
            fill_char=self.fill_char,
        )
        format_title(service, self.case)


def format_comment(
    service: IService,
    max_char: int,
    open_char: str,
    close_char: str,
    start_char: str,
    end_char: str,
    fill_char: str,
) -> None:
    def format(labeled: Labeled) -> str:
        return format_method_comment(
            method=labeled,
            max_char=max_char,
            open_char=open_char,
            close_char=close_char,
            start_char=start_char,
            end_char=end_char,
            fill_char=fill_char,
        )

    service.comments = format(labeled=service)
    for method in service.methods:
        method.comments = format(labeled=method)


def format_title(
    service: IService, case: Literal["snake", "camel", "pascal", "none"]
) -> None:
    service.name = format_title_case(service.name, case)
    for method in service.methods:
        method.name = format_title_case(method.name, case)


def format_title_case(val: str, case: Literal["snake", "camel", "pascal"]) -> str:

    case = case.strip().lower()
    if case == "snake":
        return snake_case(val)
    if case == "camel":
        return camel_case(val)
    if case == "pascal":
        return pascal_case(val)
    return val


def camel_case(val: str) -> str:
    return camelize(val, False)


def pascal_case(val: str) -> str:
    return camelize(val, True)


def format_method_comment(
    method: Labeled,
    max_char: int,
    open_char: str,
    close_char: str,
    start_char: str,
    end_char: str,
    fill_char: str,
) -> str:
    def format(text: str) -> str:
        return format_multiline(text, max_char, start_char, end_char) + "\n"

    def space_line() -> str:
        n = max_char - len(start_char) - len(end_char)
        return start_char + n * fill_char + end_char + "\n"

    title = format(" Title: " + method.title)
    spaceline = space_line()
    descriptor = format(" Description: " + method.description)
    tags = format(" Tags: " + str(method.tags))

    request_types = getattr(method, "request_types", [])
    if request_types:
        request = format(f" Request: {str(request_types[0])}")
    else:
        request = ""

    response_types = getattr(method, "response_types", [])

    if response_types:
        response = format(f" Response: {str(response_types)}")
    else:
        response = ""

    comment = format(method.comments)
    return "".join(
        [
            open_char,
            title,
            spaceline,
            descriptor,
            spaceline,
            tags,
            spaceline,
            request,
            response,
            spaceline if request else "",
            comment,
            close_char,
        ]
    )


def format_multiline(text: str, max_char: int, start_char: str, end_char: str) -> str:
    text = text.replace("\n", " ")
    count = (
        0 if not start_char else len(start_char) + 0 if not end_char else len(end_char)
    )
    max_len = max_char - count

    words = text.split()
    lines: List[str] = []
    current_line = ""

    for word in words:
        if current_line:
            if len(current_line) + 1 + len(word) > max_len:
                lines.append(current_line)
                current_line = word
            else:
                current_line += " " + word
        else:
            current_line = word

    if current_line:
        lines.append(current_line)

    formatted_lines = [
        (start_char + line).ljust(max_char, " ") + end_char for line in lines
    ]

    return "\n".join(formatted_lines)
