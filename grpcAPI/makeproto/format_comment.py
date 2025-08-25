def all_lines_start_with_double_slash(text: str) -> bool:
    if not text.startswith("//"):
        return False
    return all(
        line.strip() == "" or line.lstrip().startswith("//")
        for line in text.splitlines()
    )


def format_comment(text: str, singleline: bool = False) -> str:
    text = text.strip()
    if not text:
        return ""  # pragma: no cover

    if text.startswith("/*") and text.endswith("*/"):
        return text
    if all_lines_start_with_double_slash(text):
        return text

    lines = text.splitlines()
    if singleline:
        return "\n".join(
            line if line.strip().startswith("//") else f"// {line}" for line in lines
        )
    return f"/*\n{text}*/"
