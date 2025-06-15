import os

import pytest
from fcoverage.utils.code.pytest_utils import (
    get_test_files,
    list_fixtures_used_in_test,
    run_test_and_collect_function_coverage,
)


def test_list_fixtures(args, config):
    test_files, util_files = get_test_files(
        os.path.join(args["project"], config["tests"])
    )
    src_path = os.path.join(args["project"], config["source"])
    assert len(test_files) == 2
    test_greet = next(t for t in test_files if "test_greet" in t)
    test_calc = next(t for t in test_files if "test_calc" in t)

    fixtures = list_fixtures_used_in_test(args["project"], test_greet, src_path)

    assert len(fixtures) == 3
    assert "fixture_1" in fixtures
    assert "fixture_2" in fixtures
    assert "fixture_3" in fixtures
    assert fixtures["fixture_1"]["path"].endswith("tests/conftest.py")
    assert fixtures["fixture_2"]["path"].endswith("tests/conftest.py")
    assert fixtures["fixture_3"]["path"].endswith("tests/test_greet.py")

    fixtures = list_fixtures_used_in_test(args["project"], test_calc, src_path)
    assert len(fixtures) == 2
    assert "calculator" in fixtures
    assert "fixture_1" in fixtures, "autouse fixtures should be listed"
    assert fixtures["calculator"]["path"].endswith("tests/test_calc.py")
    assert fixtures["fixture_1"]["path"].endswith("tests/conftest.py")


@pytest.fixture
def clear_test_files(args, config):
    coverage_json_location = os.path.join(args["project"], "coverage.json")
    if os.path.exists(coverage_json_location):
        os.remove(coverage_json_location)
    yield
    if os.path.exists(coverage_json_location):
        os.remove(coverage_json_location)


def test_run_test_and_collect_function_coverage(args, config, clear_test_files):
    test_files, utils = get_test_files(os.path.join(args["project"], config["tests"]))
    src_path = os.path.join(args["project"], config["source"])
    assert len(test_files) == 2
    test_greet = next(t for t in test_files if "test_greet" in t)
    test_calc = next(t for t in test_files if "test_calc" in t)

    covered_functions = run_test_and_collect_function_coverage(
        args["project"], src_path, test_greet
    )
    assert len(covered_functions) == 1
    assert covered_functions[0] == ("src/dummy/utils/util.py", "greet")

    covered_functions = run_test_and_collect_function_coverage(
        args["project"], src_path, test_calc
    )
    assert len(covered_functions) == 2
    assert covered_functions[0] == ("src/dummy/utils/calc.py", "Calculator.add")
    assert covered_functions[1] == ("src/dummy/utils/util.py", "add_numbers")
