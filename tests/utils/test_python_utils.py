from unittest import mock
from fcoverage.utils.code.python_utils import (
    process_python_file,
)


def test_process_python_file_main(args):
    chunks = process_python_file(args["project"] + "/main.py")
    assert len(chunks) == 3
    assert chunks[0]["function_name"] == "run_greeting"
    assert chunks[1]["function_name"] == "run_addition"
    assert chunks[2]["function_name"] == "run_calculator"
    assert (
        chunks[0]["path"]
        == chunks[1]["path"]
        == chunks[2]["path"]
        == args["project"] + "/main.py"
    )
    assert chunks[0]["qualified_name"] == args["project"] + "/main.py:run_greeting"
    assert chunks[1]["qualified_name"] == args["project"] + "/main.py:run_addition"
    assert chunks[2]["qualified_name"] == args["project"] + "/main.py:run_calculator"


def test_process_python_file_calc(args):
    chunks = process_python_file(args["project"] + "/utils/calc.py")
    assert len(chunks) == 3

    assert chunks[0]["function_name"] == "Calculator.subtract"
    assert chunks[1]["function_name"] == "Calculator.multiply"
    assert chunks[2]["function_name"] == "Calculator.add"
    assert (
        chunks[0]["path"]
        == chunks[1]["path"]
        == chunks[2]["path"]
        == args["project"] + "/utils/calc.py"
    )
    assert (
        chunks[0]["qualified_name"]
        == args["project"] + "/utils/calc.py:Calculator.subtract"
    )
    assert (
        chunks[1]["qualified_name"]
        == args["project"] + "/utils/calc.py:Calculator.multiply"
    )
    assert (
        chunks[2]["qualified_name"] == args["project"] + "/utils/calc.py:Calculator.add"
    )
