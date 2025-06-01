from importlib.resources import files
import os

__all__ = [
    "get_prompt_for_feature_extraction",
    "get_prompt_for_code_summarization_module",
    "get_prompt_for_code_summarization_package",
]


def get_prompt_for_feature_extraction(filepath: str | None = None):
    return _read_prompt_file("feature_extraction.txt", filepath)


def get_prompt_for_code_summarization_module(filepath: str | None = None):
    return _read_prompt_file("code_summarization_module.txt", filepath)


def get_prompt_for_code_summarization_package(filepath: str | None = None):
    return _read_prompt_file("code_summarization_package.txt", filepath)


def _read_prompt_file(default: str, filepath: str | None = None) -> str:
    """
    Reads a prompt file from the package's data directory.
    """
    if not filepath or not os.path.exists(filepath):
        # TODO read from GitHub, or langChain, or huggingface
        template = files("fcoverage.prompts").joinpath(default)
        return template.read_text(encoding="utf-8")
    else:
        with open(filepath, "r") as file:
            return file.read()
