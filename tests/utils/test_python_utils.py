import os
from unittest import mock
from fcoverage.utils.code.python_utils import (
    build_chunks_from_python_file,
)


def test_build_chunks_from_python_file_main(args, config):
    file_path = os.path.join(args["project"], config["source"], "dummy", "main.py")
    chunks = build_chunks_from_python_file(file_path)
    assert len(chunks) == 3
    assert chunks[0]["function_name"] == "run_greeting"
    assert chunks[1]["function_name"] == "run_addition"
    assert chunks[2]["function_name"] == "run_calculator"
    assert chunks[0]["path"] == chunks[1]["path"] == chunks[2]["path"] == file_path
    assert chunks[0]["qualified_name"] == file_path + ":run_greeting"
    assert chunks[1]["qualified_name"] == file_path + ":run_addition"
    assert chunks[2]["qualified_name"] == file_path + ":run_calculator"


def test_build_chunks_from_python_file_calc(args, config):
    file_path = os.path.join(
        args["project"], config["source"], "dummy", "utils", "calc.py"
    )
    chunks = build_chunks_from_python_file(file_path)

    assert len(chunks) == 3

    assert chunks[0]["function_name"] == "Calculator.subtract"
    assert chunks[1]["function_name"] == "Calculator.multiply"
    assert chunks[2]["function_name"] == "Calculator.add"
    assert chunks[0]["path"] == chunks[1]["path"] == chunks[2]["path"] == file_path
    assert chunks[0]["qualified_name"] == file_path + ":Calculator.subtract"
    assert chunks[1]["qualified_name"] == file_path + ":Calculator.multiply"
    assert chunks[2]["qualified_name"] == file_path + ":Calculator.add"
