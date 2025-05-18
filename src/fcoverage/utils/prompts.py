from importlib.resources import files

__all__ = [
    "get_prompt_for_code_completion",
]


def get_prompt_for_feature_extraction():
    return _read_prompt_file("feature_extraction.txt")


def _read_prompt_file(file_name: str) -> str:
    """
    Reads a prompt file from the package's data directory.
    """
    template = files("fcoverage.prompts").joinpath(file_name)
    return template.read_text(encoding="utf-8")
