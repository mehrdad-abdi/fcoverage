from importlib.resources import files

__all__ = [
    "read_prompt_file",
]


def read_prompt_file(file_name: str) -> str:
    """
    Reads a prompt file from the package's data directory.
    """
    template = files("fcoverage.prompts").joinpath(file_name)
    return template.read_text(encoding="utf-8")
