import ast
import os
import hashlib
from typing import Dict, List, Set, Tuple
from enum import Enum


class CodeType(str, Enum):
    FUNCTION: str = "function"
    CLASS: str = "class"
    CLASS_METHOD: str = "method"
    Other: str = "other"


def hash_text_content(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def is_valid_python_file(file_path: str) -> bool:
    return file_path.endswith(".py")


def get_all_python_files(source_dir: str) -> List[str]:
    python_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            if is_valid_python_file(file):
                python_files.append(os.path.join(root, file))
    return python_files


def build_chunks_from_python_file(
    file_path: str,
) -> Tuple[List[Dict], Set[Tuple[str, str]]]:
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


def get_qualified_name(file_path, class_name, name, type_: CodeType):
    match type_:
        case CodeType.CLASS:
            return f"{file_path}:{name}"
        case CodeType.FUNCTION:
            return f"{file_path}::{name}"
        case CodeType.CLASS_METHOD:
            return f"{file_path}:{class_name}:{name}"
    raise ValueError(f"Unknow parameters ({file_path, class_name, name, type_})")


class FunctionChunksExtractor(ast.NodeVisitor):

    def __init__(self, filename: str, source_code: str):
        self.filename = filename
        self.source_code = source_code
        self.current_class = None
        self.defined_functions = set()
        self.chunks = dict()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.current_class:
            _type = CodeType.CLASS_METHOD
        else:
            _type = CodeType.FUNCTION
        self.keep(node, _type)
        # stop visiting childs --> skip nested functions

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.keep(node, CodeType.CLASS)
        self.generic_visit(node)
        self.current_class = None

    def keep(self, node, code_type: CodeType):
        name = node.name
        qualified_name = get_qualified_name(
            self.filename, self.current_class, name, code_type
        )

        if code_type in [CodeType.FUNCTION, CodeType.CLASS_METHOD]:
            self.defined_functions.add(qualified_name)

        code_chunk = ast.get_source_segment(self.source_code, node)
        self.chunks[qualified_name] = {
            "name": name,
            "class_name": self.current_class,
            "type": code_type,
            "qualified_name": qualified_name,
            "code": code_chunk,
            "hash": hash_text_content(code_chunk),
            "path": self.filename,
            "start_line": node.lineno - 1,
            "end_line": node.end_lineno if hasattr(node, "end_lineno") else None,
        }
