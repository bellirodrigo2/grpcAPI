from typing import Dict

from inflection import camelize
from inflection import underscore as snake_case
from typing_extensions import Any, List, Literal, Mapping, Optional, Protocol, Tuple

from grpcAPI.makeproto import IService
from grpcAPI.makeproto.interface import ILabeledMethod
from grpcAPI.process_service import ProcessService


class Labeled(Protocol):
    comments: str
    title: str
    description: str
    tags: List[str]


# class FormatServiceFactory:
#     def __call__(self, settings: Mapping[str, Any]) -> "FormatService":

#         max_char, title_case, comment_strategy = get_format_settings(settings)
#         max_char = max_char or 80
#         title_case = title_case or "none"
#         comment_strategy = comment_strategy or "multiline"

#         return FormatService(max_char, title_case, comment_strategy)


def get_format_settings(
    settings: Mapping[str, Any],
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    format_settings = settings.get("format", {})
    max_char = format_settings.get("max_char_per_line", None)
    case = format_settings.get("case", None)
    comment_strategy = format_settings.get("comment_style", None)
    return max_char, case, comment_strategy


class FormatService(ProcessService):

    def __init__(self, **kwargs: Any) -> None:

        format_settings: Dict[str, Any] = kwargs.get("format", {})

        max_char = int(format_settings.get("max_char_per_line", 80))
        case = format_settings.get("title_case", "none")
        strategy = format_settings.get("comment_style", "multiline")

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

    def __format_comment(self, labeled: Labeled) -> str:
        return format_method_comment(
            method=labeled,
            max_char=self.max_char,
            open_char=self.open_char,
            close_char=self.close_char,
            start_char=self.start_char,
            end_char=self.end_char,
            fill_char=self.fill_char,
        )

    def _process_method(self, method: ILabeledMethod) -> None:
        method.comments = self.__format_comment(labeled=method)
        method.name = format_title_case(method.name, self.case)

    def _process_service(self, service: IService) -> None:
        service.comments = self.__format_comment(labeled=service)
        service.name = format_title_case(service.name, self.case)


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
    """
    Formats the text into multiple lines with a prefix and suffix per line, respecting the maximum line length.

    - Ensures that each line has at most `max_char` characters in total, including `start_char` and `end_char`.
    - Splits long words if necessary.
    """
    text = text.replace("\n", " ").strip()
    words = text.split()

    prefix_len = len(start_char)
    suffix_len = len(end_char)
    available_len = max_char - prefix_len - suffix_len
    if available_len <= 0:
        available_len = prefix_len + suffix_len + 1

    lines: List[str] = []
    current_line = ""

    for word in words:
        while len(word) > available_len:
            part = word[:available_len]
            lines.append(f"{start_char}{part.ljust(available_len)}{end_char}")
            word = word[available_len:]

        if len(current_line) + len(word) + (1 if current_line else 0) > available_len:
            lines.append(f"{start_char}{current_line.ljust(available_len)}{end_char}")
            current_line = word
        else:
            current_line += (" " if current_line else "") + word

    if current_line:
        lines.append(f"{start_char}{current_line.ljust(available_len)}{end_char}")

    return "\n".join(lines)
