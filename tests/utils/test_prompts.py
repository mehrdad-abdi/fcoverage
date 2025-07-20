from fcoverage.utils.prompts import escape_markdown, wrap_in_code_block


def test_escape_markdown():
    result = escape_markdown("```\nEscape this text\n```\n")
    assert "```" not in result


def test_wrap_in_code_block():
    result = wrap_in_code_block("```\nEscape this text\n```\n")
    assert result.startswith("```")
    assert result.endswith("```")
    assert "```" not in result[3:-3]
