from unittest import mock
from fcoverage.utils.code.python_utils import (
    process_python_file,
)

FAKE_SRC_MAIN = """
import os
from lib.lib import greet, add_numbers as do_sum
from lib.lib2 import Calculator

def run_greeting():
    name = "Alice"
    print(greet(name))
    print("Available CPUs: ", os.cpu_count())


def run_addition():
    a, b = 5, 7
    print(f"{a} + {b} = {do_sum(a, b)}")

def run_calculator():
    calc = Calculator()
    calc.bias = 1
    x, y = 10, 2
    print(f"{x} - {y} = {calc.subtract(x, y)}")
    print(f"{x} * {y} = {calc.multiply(x, y)}")

if __name__ == "__main__":
    run_greeting()
    run_addition()
    run_calculator()
"""
FAKE_SRC_LIB = """
def greet(name):
    return f"Hello, {name}!"

def add_numbers(a, b):
    return a + b

"""
FAKE_SRC_LIB2 = """
from lib.lib import greet, add_numbers

class Calculator:
    bias = 0
    def subtract(self, a, b):
        return self.bias + a - b

    def multiply(self, a, b):
        return self.bias + (a * b)

    def add(self, a, b):
        return self.bias + add_numbers(a, b)
"""

FILES = {
    "foo/main.py": FAKE_SRC_MAIN,
    "foo/lib/lib.py": FAKE_SRC_LIB,
    "foo/lib/lib2.py": FAKE_SRC_LIB2,
}


def side_effect_for_open(filename, *argsx, **kwargsx):
    if filename == "foo/main.py":
        return mock.mock_open(read_data=FAKE_SRC_MAIN)()
    elif filename == "foo/lib/lib.py":
        return mock.mock_open(read_data=FAKE_SRC_LIB)()
    elif filename == "foo/lib/lib2.py":
        return mock.mock_open(read_data=FAKE_SRC_LIB2)()
    else:
        raise ValueError(f"File {filename} not found.")


def test_process_python_file_main():
    with mock.patch("builtins.open") as mock_file:
        mock_file.side_effect = side_effect_for_open
        chunks = process_python_file("foo/main.py")
    assert len(chunks) == 3
    assert chunks[0]["function_name"] == "run_greeting"
    assert chunks[1]["function_name"] == "run_addition"
    assert chunks[2]["function_name"] == "run_calculator"
    assert chunks[0]["path"] == chunks[1]["path"] == chunks[2]["path"] == "foo/main.py"
    assert chunks[0]["qualified_name"] == "foo/main.py:run_greeting"
    assert chunks[1]["qualified_name"] == "foo/main.py:run_addition"
    assert chunks[2]["qualified_name"] == "foo/main.py:run_calculator"


def test_process_python_file_lib2():
    with mock.patch("builtins.open") as mock_file:
        mock_file.side_effect = side_effect_for_open
        chunks = process_python_file("foo/lib/lib2.py")
    assert len(chunks) == 3

    assert chunks[0]["function_name"] == "Calculator.subtract"
    assert chunks[1]["function_name"] == "Calculator.multiply"
    assert chunks[2]["function_name"] == "Calculator.add"
    assert (
        chunks[0]["path"] == chunks[1]["path"] == chunks[2]["path"] == "foo/lib/lib2.py"
    )
    assert chunks[0]["qualified_name"] == "foo/lib/lib2.py:Calculator.subtract"
    assert chunks[1]["qualified_name"] == "foo/lib/lib2.py:Calculator.multiply"
    assert chunks[2]["qualified_name"] == "foo/lib/lib2.py:Calculator.add"
