from grpcAPI.makeproto.format_comment import (
    all_lines_start_with_double_slash,
    format_comment,
)


def test_format_comment() -> None:
    # Test 1: Empty text should return empty
    result = format_comment("")
    assert result == "", f"Expected empty string, got: '{result}'"

    # Test 2: Already valid block comment should be returned unchanged
    block_comment = "/* This is a valid block comment */"
    result = format_comment(block_comment)
    assert (
        result == block_comment
    ), f"Block comment should remain unchanged. Got: '{result}'"

    # Test 3: Already valid single line comment should be returned unchanged
    single_line_comment = "// This is a valid comment"
    result = format_comment(single_line_comment)
    assert (
        result == single_line_comment
    ), f"Single line comment should remain unchanged. Got: '{result}'"

    # Test 4: Multiple lines with // should be returned unchanged
    multi_line_comment = """// First line
// Second line
// Third line"""
    result = format_comment(multi_line_comment)
    assert (
        result == multi_line_comment
    ), f"Multi-line // comment should remain unchanged. Got: '{result}'"

    # Test 5: Simple text should be converted to single line comment
    simple_text = "This is simple text"
    result = format_comment(simple_text, singleline=True)
    expected = "// This is simple text"
    assert result == expected, f"Expected: '{expected}', got: '{result}'"

    # Test 6: Multiple lines should be converted to single line comments
    multi_line_text = """First line
Second line
Third line"""
    result = format_comment(multi_line_text, singleline=True)
    expected = """// First line
// Second line
// Third line"""
    assert result == expected, f"Expected: '{expected}', got: '{result}'"

    # Test 7: Text should be converted to block comment when singleline=False
    simple_text = "This is simple text"
    result = format_comment(simple_text, singleline=False)
    expected = "/*\nThis is simple text*/"
    assert result == expected, f"Expected: '{expected}', got: '{result}'"

    # Test 8: Multiple lines should be converted to block comment
    multi_line_text = """First line
Second line
Third line"""
    result = format_comment(multi_line_text, singleline=False)
    expected = "/*\nFirst line\nSecond line\nThird line*/"
    assert result == expected, f"Expected: '{expected}', got: '{result}'"

    # Test 9: Mixed lines (some with //, others without) in singleline mode
    mixed_text = """// Already a comment
This line is not a comment
// This one is also already a comment"""
    result = format_comment(mixed_text, singleline=True)
    expected = """// Already a comment
// This line is not a comment
// This one is also already a comment"""
    assert result == expected, f"Expected: '{expected}', got: '{result}'"

    # Test 10: Empty lines should be preserved
    text_with_empty_lines = """First line

Third line"""
    result = format_comment(text_with_empty_lines, singleline=True)
    expected = """// First line
// 
// Third line"""
    assert result == expected, f"Expected: '{expected}', got: '{result}'"


def test_all_lines_start_with_double_slash() -> None:
    # Test 1: Text that doesn't start with // should return False
    text = "This text is not a comment"
    result = all_lines_start_with_double_slash(text)
    assert not result, f"Expected False for non-comment text, got: {result}"

    # Test 2: Single line comment should return True
    text = "// This is a comment"
    result = all_lines_start_with_double_slash(text)
    assert result, f"Expected True for single line comment, got: {result}"

    # Test 3: Multiple lines with // should return True
    text = """// First line
// Second line
// Third line"""
    result = all_lines_start_with_double_slash(text)
    assert result, f"Expected True for multi-line comment, got: {result}"

    # Test 4: Multiple lines with some without // should return False
    text = """// First line
Second line without //
// Third line"""
    result = all_lines_start_with_double_slash(text)
    assert not result, f"Expected False for mixed content, got: {result}"

    # Test 5: Text with empty lines should return True if other lines have //
    text = """// First line

// Third line"""
    result = all_lines_start_with_double_slash(text)
    assert result, f"Expected True for comment with empty lines, got: {result}"


if __name__ == "__main__":
    test_all_lines_start_with_double_slash()
    test_format_comment()
