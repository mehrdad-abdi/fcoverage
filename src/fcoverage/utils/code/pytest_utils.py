import os
from pathlib import Path
import subprocess


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
        if "--" in line
        and "---" not in line
        and not line.startswith(" ")
        and "..." not in line
    ]
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
