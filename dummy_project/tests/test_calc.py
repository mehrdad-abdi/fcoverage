import pytest
from dummy.utils.calc import Calculator


class TestCalculator:

    @pytest.fixture
    def calculator(self):
        return Calculator()

    def test_greet(self, calculator):
        assert calculator.add(1, 2) == 3
