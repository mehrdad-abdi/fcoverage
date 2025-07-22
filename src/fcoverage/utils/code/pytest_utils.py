from pathlib import Path


def get_test_files(str_src_path: str):
    src_path = Path(str_src_path).resolve()
    test_files = set()
    for path in src_path.rglob("test_*.py"):
        if path.is_file():
            test_files.add(str(path))
    for path in src_path.rglob("*_test.py"):
        if path.is_file():
            test_files.add(str(path))

    return list(test_files)
