import json
import os
from pathlib import Path
import subprocess
from itertools import chain
from fcoverage.utils.code.python_utils import (
    build_chunks_from_python_file,
)


def get_test_files(src_path: str):
    src_path = Path(src_path).resolve()
    test_files = set()
    util_files = set()
    for path in chain(src_path.rglob("test_*.py"), src_path.rglob("*_test.py")):
        if path.is_file():
            test_files.add(str(path))
        else:
            util_files.add(str(path))

    return list(test_files), list(util_files)


def list_available_fixtures(project_root, test_path, pythonpath: str = None):
    test_path_relative = Path(test_path).relative_to(project_root)
    cmd_out = run_cmd(
        "pytest --fixtures-per-test --fixtures -q " + str(test_path_relative),
        project_root,
        pythonpath=pythonpath,
    )
    fixtures = {}
    lines = [
        line
        for line in cmd_out
        if "--" in line and "---" not in line and not line.startswith(" ")
    ]
    for line in lines:
        parts = line.split("--", 1)

        fixture_name = parts[0].strip()
        fixture_path, line_number = parts[1].strip().split(":", 1)
        if fixture_path.startswith("..."):
            continue
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
    test_path_relative = Path(test_path).relative_to(project_root)
    cmd_out = run_cmd(
        "pytest --setup-only -q --setup-show " + str(test_path_relative),
        project_root,
        pythonpath=pythonpath,
    )
    fixtures = {}
    fixtures = [line.split()[2] for line in cmd_out if "SETUP" in line]

    defined_fixtures = list_available_fixtures(
        project_root, test_path, pythonpath=pythonpath
    )
    used_fixtures = dict()
    chunks = dict()
    for k, v in defined_fixtures.items():
        if k in fixtures:
            if v["path"] not in chunks:
                chunks[v["path"]] = build_chunks_from_python_file(
                    os.path.join(project_root, v["path"])
                )[0]
            fixture_chunks = [
                chunk for chunk in chunks[v["path"]].values() if chunk["name"] == k
            ]
            if len(fixture_chunks) == 0:
                # this shouldn't happen. If happens, file a bug ticket!
                continue
            if len(fixture_chunks) > 1:
                # In rare cases, the name of function and the name of class method can be equals.
                fixture_chunks = [
                    c
                    for c in fixture_chunks
                    if c["start_line"] <= v["line_number"] <= c["end_line"]
                ]
            chunk = fixture_chunks[0]
            used_fixtures[k] = chunk
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
