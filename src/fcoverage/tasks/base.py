from json import tool
import json
import os
from pathlib import Path
from typing import Dict, List
from fcoverage.models import FeatureItem
from fcoverage.utils import prompts
from langchain.chat_models import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor

from fcoverage.utils.vdb import VectorDBHelper


class TasksBase:
    def __init__(self, args):
        self.args = args
        self.project_name = self.args["project-name"]
        self.project_description = self.args["project-description"]
        self.project_src = os.path.join(self.args["project"], self.args["src-path"])
        self.project_tests = os.path.join(self.args["project"], self.args["test-path"])
        self.model = None
        self.vdb = None

    def prepare(self):
        self.load_llm_model()
        self.load_vector_db_helper()

    def run(self):
        raise NotImplementedError("Subclasses must implement this method")

    def load_prompt(self, prompt_filename):
        return prompts.read_prompt_file(prompt_filename)

    def load_llm_model(self):
        model_name = self.args.get("llm-model")
        model_provider = self.args.get("llm-provider")

        self.model = init_chat_model(
            model_name,
            model_provider=model_provider,
        )

    def load_vector_db_helper(self):
        self.vdb = VectorDBHelper(
            persist_directory=self.args["vector-db-persist"],
            collection_name="fcoverage",
            embedding_model=self.args["embedding-model"],
            embedding_provider=self.args["embedding-provider"],
        )

    def get_tool_calling_llm(self, tools, prompt_template, memory=None, verbose=False):
        agent = create_tool_calling_agent(
            llm=self.model,
            tools=tools,
            prompt=prompt_template,
        )
        return AgentExecutor(agent=agent, tools=tools, verbose=verbose, memory=memory)

    @tool
    def search_vector_db(self, query: str, k: int = 5) -> List[str]:
        """Search the vector DB for chunks related to a natural language query."""
        results = self.vdb.search(query, k=k)
        return [
            f"[{doc.metadata.get('source')}]\n{doc.page_content}" for doc in results
        ]

    @tool
    def load_file_section(self, path: str, start: int, end: int) -> str:
        """Load specific lines from a file."""
        try:
            with open(path, "r") as f:
                lines = f.readlines()
            return "".join(lines[start - 1 : end])
        except Exception as e:
            return f"Error reading file: {e}"

    @tool
    def grep_string(
        self, search: str, page_size: int = 10, page: int = 1
    ) -> List[Dict[str, str]]:
        """Search for a string in code files and return matching lines with file name and line number. Supports pagination."""
        result = []
        for file in Path(self.args["project"]).rglob("*.py"):
            try:
                with open(file, "r", errors="ignore") as f:
                    for lineno, line in enumerate(f, start=1):
                        if search in line:
                            result.append(
                                {
                                    "file": str(file),
                                    "line": lineno,
                                    "text": line.strip(),
                                }
                            )
            except Exception as e:
                result.append(
                    {"file": str(file), "line": -1, "text": f"Error reading file: {e}"}
                )

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        return result[start_index:end_index]

    @tool
    def list_directory(self, path: str) -> List[Dict[str, str]]:
        """List files and folders in a directory with metadata (type file or dir, size in kb if it's file, children count if a dir)."""

        path_abs = os.path.join(self.args["project"], path)
        path_obj = Path(path_abs)
        if not path_obj.exists():
            return [{"error": f"Path '{path}' does not exist."}]
        if not path_obj.is_dir():
            return [{"error": f"Path '{path}' is not a directory."}]

        results = []
        for item in path_obj.iterdir():
            if item.is_file():
                size_kb = round(item.stat().st_size / 1024, 2)
                results.append(
                    {"name": item.name, "type": "file", "size": f"{size_kb} KB"}
                )
            elif item.is_dir():
                num_files = sum(1 for f in item.iterdir() if f.is_file())
                num_dirs = sum(1 for f in item.iterdir() if f.is_dir())
                results.append(
                    {
                        "name": item.name,
                        "type": "dir",
                        "children": f"{num_files} file(s), {num_dirs} dir(s)",
                    }
                )
            else:
                results.append(
                    {
                        "name": item.name,
                        "type": "other",
                    }
                )
        return results

    def load_feature_item(self):
        definition_filepath = self.args["feature-definition"]
        with open(definition_filepath, "r") as f:
            feature_item_json = json.load(f)
        return FeatureItem(**feature_item_json)

    def load_feature_implementation(self):
        design = self.args["feature-design"]
        with open(design, "r") as f:
            content = f.read()
        return content

    def load_test_cases(self):
        test_cases = self.args["feature-test-cases"]
        with open(test_cases, "r") as f:
            content = f.read()
        return content
