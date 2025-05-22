import pytest
from dummy.utils.util import greet


@pytest.fixture
def fixture_3(fixture_2):
    return f"fixture_1-{fixture_2}"


def test_greet(fixture_3):
    assert greet(fixture_3) == "Hello, fixture_1-fixture_2(fixture_1)!"
