import ast
import os
from typing import Dict, List, Set, Tuple


def is_valid_python_file(file_path: str) -> bool:
    return file_path.endswith(".py")


def get_all_python_files(source_dir: str) -> List[str]:
    python_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            if is_valid_python_file(file):
                python_files.append(os.path.join(root, file))
    return python_files


def process_python_file(file_path: str) -> Tuple[List[Dict], Set[Tuple[str, str]]]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        tree = ast.parse(source_code)

        extractor = FunctionChunksExtractor(file_path, source_code)
        extractor.visit(tree)
        return extractor.chunks
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")
        return [], []


class FunctionChunksExtractor(ast.NodeVisitor):

    def __init__(self, filename: str, source_code: str):
        self.filename = filename
        self.source_code = source_code
        self.current_function = None
        self.current_class = None
        self.defined_functions = set()
        self.chunks = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        function_name = node.name
        if self.current_class:
            function_name = f"{self.current_class}.{function_name}"
        qualified_name = f"{self.filename}:{function_name}"
        code_chunk = ast.get_source_segment(self.source_code, node)
        self.defined_functions.add(qualified_name)
        self.current_function = qualified_name
        self.chunks.append(
            {
                "function_name": function_name,
                "qualified_name": qualified_name,
                "code": code_chunk,
                "path": self.filename,
                "start_line": node.lineno - 1,
                "end_line": node.end_lineno if hasattr(node, "end_lineno") else None,
            }
        )
        self.generic_visit(node)
        self.current_function = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None
