from importlib.resources import files
import os

__all__ = [
    "load_prompts",
]


def load_prompts(prompt_filename, custom_prompts_path: str = None):
    custom_prompts_path = os.path.join(
        custom_prompts_path,
        prompt_filename,
    )
    if not os.path.exists(custom_prompts_path):
        return _read_prompt_file(prompt_filename)
    else:
        with open(custom_prompts_path, "r") as file:
            return file.read()


def _read_prompt_file(file_name: str) -> str:
    """
    Reads a prompt file from the package's data directory.
    """
    template = files("fcoverage.prompts").joinpath(file_name)
    return template.read_text(encoding="utf-8")
