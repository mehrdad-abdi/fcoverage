import os

from fcoverage.utils.code.pytest_utils import (
    get_test_files,
    list_available_fixtures,
)


def test_list_fixtures(args, config):
    test_files = get_test_files(os.path.join(args["project"], config["tests"]))
    src_path = os.path.join(args["project"], config["source"])
    assert len(test_files) == 2
    test_greet = next(t for t in test_files if "test_greet" in t)

    fixtures = list_available_fixtures(args["project"], test_greet, src_path)

    assert len(fixtures) == 3
    assert "fixture_1" in fixtures
    assert "fixture_2" in fixtures
    assert "fixture_3" in fixtures
    assert fixtures["fixture_1"]["path"] == "tests/conftest.py"
    assert fixtures["fixture_2"]["path"] == "tests/conftest.py"
    assert (
        fixtures["fixture_3"]["path"] == "tests/test_greet.py"
    ), "fixture precendence should be respected"
