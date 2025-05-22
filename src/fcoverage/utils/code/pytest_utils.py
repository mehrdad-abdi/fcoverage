import json
import os
from pathlib import Path
import coverage
import subprocess
from fcoverage.utils.code.python_utils import build_chunks_from_python_file


def get_test_files(src_path: str):
    src_path = Path(src_path).resolve()
    test_files = set()
    for path in src_path.rglob("test_*.py"):
        if path.is_file():
            test_files.add(str(path))
    for path in src_path.rglob("*_test.py"):
        if path.is_file():
            test_files.add(str(path))

    return list(test_files)


def list_available_fixtures(project_root, test_path, pythonpath: str = None):
    cmd_out = run_cmd(
        "pytest --fixtures-per-test --fixtures -q " + test_path,
        project_root,
        pythonpath=pythonpath,
    )
    fixtures = {}
    lines = [line for line in cmd_out if "--" in line and "---" not in line]
    for line in lines:
        parts = line.split("--", 1)

        fixture_name = parts[0].strip()
        fixture_path, line_number = parts[1].strip().split(":", 1)
        is_in_project = os.path.abspath(
            os.path.join(project_root, fixture_path)
        ).startswith(project_root)
        if not is_in_project:
            continue
        fixtures[fixture_name] = {
            "path": fixture_path,
            "line_number": line_number,
        }
    return fixtures


def list_fixtures_used_in_test(project_root, test_path, pythonpath: str = None):
    cmd_out = run_cmd(
        "pytest --setup-only -q --setup-show " + test_path,
        project_root,
        pythonpath=pythonpath,
    )
    fixtures = {}
    fixtures = [line.split()[2] for line in cmd_out if "SETUP" in line]

    defined_fixtures = list_available_fixtures(
        project_root, test_path, pythonpath=pythonpath
    )
    used_fixtures = {k: v for k, v in defined_fixtures.items() if k in fixtures}

    return used_fixtures


def run_cmd(command: str, working_directory, pythonpath: str = None):
    print(f"Running command: {command} in {working_directory}")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
        cwd=working_directory,
        env={"PYTHONPATH": pythonpath, **dict(os.environ)} if pythonpath else None,
    )
    if result.returncode != 0:
        print("Error:", result.stderr)
    return result.stdout.splitlines()


def run_test_and_collect_function_coverage(
    root_dir: str, src_path: str, test_target: str
):
    print(f"Measuring coverage: {test_target} in {root_dir} against {src_path}")
    src_path_relative = Path(src_path).relative_to(root_dir)

    run_cmd(
        f"pytest --cov={src_path_relative} --cov-report=json -q --tb=short --disable-warnings {test_target}",
        root_dir,
        pythonpath=str(src_path),
    )

    with open(os.path.join(root_dir, "coverage.json"), "r") as f:
        coverage_report = json.load(f)

    covered_functions = set()

    for file_name, coverage_info in coverage_report["files"].items():
        for function_name, function_coverage in coverage_info["functions"].items():
            if function_name and function_coverage["executed_lines"]:
                covered_functions.add((file_name, function_name))

    return sorted(covered_functions, key=lambda x: (x[0], x[1]))
