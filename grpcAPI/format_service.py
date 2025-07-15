from inflection import camelize
from inflection import underscore as snake_case
from makeproto import IService
from typing_extensions import Literal

from grpcAPI.app import APIService
from grpcAPI.interfaces import Labeled
from grpcAPI.types import LabeledMethod


def format_service(
    service: IService, max_char: int, case: Literal["snake", "camel", "pascal", "none"]
) -> None:
    format_comment(service, max_char, "* ")
    format_title(service, case)


def format_comment(service: IService, max_char: int, start_char: str) -> None:
    service.comments = format_method_comment(service, max_char, start_char)
    for method in service.methods:
        method.comments = format_method_comment(method, max_char, start_char)


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


def format_method_comment(method: Labeled, max_char: int, start_char: str) -> str:
    line0 = "/*\n"
    title = start_char + "Method: " + method.title + "\n"
    space1 = start_char + "\n"
    descriptor = (
        start_char
        + "Description: "
        + format_multiline(method.description, max_char, "")
        + "\n"
    )
    space2 = start_char + "\n"
    tags = format_multiline("Tags: " + str(method.tags), max_char, "* ") + "\n"
    space3 = start_char + "\n"
    comment = format_multiline(method.comments, max_char, start_char)
    linef = "\n*/"
    return "".join(
        [line0, title, space1, descriptor, space2, tags, space3, comment, linef]
    )


def format_multiline(text: str, max_char: int, start_char: str) -> str:
    text = text.replace("\n", " ")
    max_len = max_char - 1

    words = text.split()
    lines = []
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

    formatted_lines = [start_char + line for line in lines]

    return "\n".join(formatted_lines)


if __name__ == "__main__":
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."

    service = APIService(name="Teste", comments=text)
    print(format_service_comment(service, 80, "* "))

    method = LabeledMethod(
        "teste",
        lambda: "foo",
        "",
        "",
        "",
        text,
        "this method is intended to solve a problem",
        [],
        [
            "foo",
            "bar",
            "consectetur",
            "dfqwdkwqodkqwokdowqkdwq",
            "ewofweofweofwef",
            "hello",
            "world",
        ],
        [],
        None,
    )
    print(format_method_comment(method, 80, "* "))
