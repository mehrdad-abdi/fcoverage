from importlib.resources import files

__all__ = [
    "read_prompt_file",
    "escape_markdown",
    "wrap_in_code_block",
]


def escape_markdown(text):
    # Escape common markdown characters
    escaped_text = text.replace("```", "``\\`")
    # return re.sub(r"([\\`*_{}[\]()#+\-!])", r"\\\1", text)
    return escaped_text


def wrap_in_code_block(text):
    # Escape triple backticks inside the text to prevent breaking the code block
    return f"```\n{escape_markdown(text)}\n```"


def read_prompt_file(file_name: str) -> str:
    """
    Reads a prompt file from the package's data directory.
    """
    template = files("fcoverage.prompts").joinpath(file_name)
    return template.read_text(encoding="utf-8")
