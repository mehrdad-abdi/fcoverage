import pytest
from dummy.utils.calc import Calculator


@pytest.fixture
def calculator():
    return Calculator()


def test_greet(calculator):
    assert calculator.add(1, 2) == 3
