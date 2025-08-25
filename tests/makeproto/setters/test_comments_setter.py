from grpcAPI.makeproto.format_comment import format_comment


def test_already_single_line_comment() -> None:
    comment = "// existing comment"
    assert format_comment(comment) == comment


def test_already_multiline_comment() -> None:
    comment = "/* multiline comment */"
    assert format_comment(comment) == comment


def test_single_line_under_max_chars() -> None:
    assert (
        format_comment("short description", singleline=True) == "// short description"
    )


def test_single_line_equals_max_chars() -> None:
    text = "a" * 50
    assert format_comment(text, singleline=True) == f"// {text}"


def test_multiline_comment() -> None:
    text = "This is a very long description that is \n split into multiple lines"
    expected = (
        "// This is a very long description that is \n//  split into multiple lines"
    )
    assert format_comment(text, singleline=True) == expected


def test_multiline_comment2() -> None:
    text = "// This is a very long description that is \n split into multiple lines"
    expected = (
        "// This is a very long description that is \n//  split into multiple lines"
    )
    assert format_comment(text, singleline=True) == expected
