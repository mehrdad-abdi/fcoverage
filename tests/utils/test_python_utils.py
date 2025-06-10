import os
from fcoverage.utils.code.python_utils import (
    CodeType,
    build_chunks_from_python_file,
)


def test_build_chunks_from_python_file_main(args, config):
    file_path = os.path.join(args["project"], config["source"], "dummy", "main.py")
    chunks = build_chunks_from_python_file(file_path)
    assert len(chunks) == 3
    assert f"{file_path}::run_greeting" in chunks
    assert f"{file_path}::run_addition" in chunks
    assert f"{file_path}::run_calculator" in chunks

    assert chunks[f"{file_path}::run_greeting"]["name"] == "run_greeting"
    assert chunks[f"{file_path}::run_addition"]["name"] == "run_addition"
    assert chunks[f"{file_path}::run_calculator"]["name"] == "run_calculator"
    assert all(chunk["path"] == file_path for chunk in chunks.values())
    assert all(chunk["type"] == CodeType.FUNCTION for chunk in chunks.values())


def test_build_chunks_from_python_file_calc(args, config):
    file_path = os.path.join(
        args["project"], config["source"], "dummy", "utils", "calc.py"
    )
    chunks = build_chunks_from_python_file(file_path)

    assert len(chunks) == 4
    assert f"{file_path}:Calculator" in chunks
    assert f"{file_path}:Calculator:subtract" in chunks
    assert f"{file_path}:Calculator:multiply" in chunks
    assert f"{file_path}:Calculator:add" in chunks

    assert all(chunk["path"] == file_path for chunk in chunks.values())
    assert chunks[f"{file_path}:Calculator"]["type"] == CodeType.CLASS
    assert chunks[f"{file_path}:Calculator:subtract"]["type"] == CodeType.CLASS_METHOD
