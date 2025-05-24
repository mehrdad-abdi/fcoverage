import pytest


@pytest.fixture(autouse=True)
def fixture_1():
    return "fixture_1"


@pytest.fixture
def fixture_2(fixture_1):
    return f"fixture_2({fixture_1})"


@pytest.fixture
def fixture_3():
    return "FOOO"
