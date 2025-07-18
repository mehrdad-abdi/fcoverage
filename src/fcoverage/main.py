import json
import sys
import argparse
import os
from fcoverage.tasks import (
    FeatureExtractionTask,
    AnalyseTestsTask,
    CodeAnalysisTask,
)

def run_task(args):
    if args["task"] == "catalog":
        task = FeatureExtractionTask(args=args)
    elif args["task"] == "manifest":
        task = CodeAnalysisTask(args=args)
    elif args["task"] == "coverage":
        task = AnalyseTestsTask(args=args)
    task.prepare()
    return task.run()


def main():
    args = get_args()

    config = load_config(args.project)
    print(yaml.dump(config, indent=2))
    print(json.dumps(dict(os.environ), indent=2))

    if not run_task(vars(args), config):
        return 1
    return 0


def get_args():
    parser = argparse.ArgumentParser(description="Feature Coverage Analysis Tool")
    parser.add_argument(
        "--gitthub",
        type=str,
        help="The GitHub address of the project.",
        required=False,
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Path to the project directory.",
        required=True,
    )
    parser.add_argument(
        "--task",
        choices=[
            "catalog",
            "manifest",
            "coverage",
        ],
        help="Task to run.",
        required=True,
    )
    parser.add_argument(
        "--only-file",
        help="Run the task only on this file.",
    )
    parser.add_argument(
        "--vector-db-persist",
        help="The path to store the vector database.",
        default="vector-db"
    )
    parser.add_argument(
        "--src-path",
        help="The folder containing source codes within the project root.",
        default="src"
    )
    parser.add_argument(
        "--test-path",
        help="The folder containing test codes within the project root.",
        default="test"
    )
    parser.add_argument(
        "--llm-model",
        help="The name of llm model. See https://python.langchain.com/docs/integrations/chat/.",
        default="gemini-2.0-flash"
    )
    parser.add_argument(
        "--llm-provider",
        help="The name of llm model provider. See https://python.langchain.com/docs/integrations/chat/.",
        default="google_genai"
    )
    parser.add_argument(
        "--embedding-model",
        help="The name of embedding model. See https://python.langchain.com/docs/integrations/chat/.",
        default="text-embedding-3-large"
    )
    parser.add_argument(
        "--embedding-provider",
        help="The name of llm embedding provider. See https://python.langchain.com/docs/integrations/chat/.",
        default="openai"
    )
    parser.add_argument(
        "--feature-definition",
        help="The path of feature definition file. Required in manifest task",
        default=""
    )
    parser.add_argument(
        "--feature-manifest",
        help="The path of feature manifest file. Required in coverage task",
        default=""
    )
    
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    sys.exit(main())
