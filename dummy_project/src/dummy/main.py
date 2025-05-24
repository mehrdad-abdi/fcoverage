import os
from dummy.utils.util import greet, add_numbers as do_sum
from dummy.utils.calc import Calculator


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
