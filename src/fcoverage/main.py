import json
import sys
import yaml
import argparse
import os
from fcoverage.tasks import (
    FeatureExtractionTask,
    AnalyseTestsTask,
    CodeAnalysisTask,
    CodeSummarizationTask,
)

DEFAULT_HOME = ".fcoverage"
DEFAULT_CONFIG_PATH = f"{DEFAULT_HOME}/config.yml"


def load_config(project_path):
    config_file_path = os.path.join(os.path.abspath(project_path), DEFAULT_CONFIG_PATH)
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(
            f"Configuration file not found: {os.path.abspath(config_file_path)}"
        )
    with open(config_file_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def run_task(args, config):
    if args["task"] == "feature-extraction":
        task = FeatureExtractionTask(args=args, config=config)
    elif args["task"] == "code-analysis":
        task = CodeAnalysisTask(args=args, config=config)
    elif args["task"] == "test-analysis":
        task = AnalyseTestsTask(args=args, config=config)
    elif args["task"] == "code-summary":
        task = CodeSummarizationTask(args=args, config=config)
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
        help=f"The GitHub address of the project.",
        required=False,
    )
    parser.add_argument(
        "--project",
        type=str,
        help=f"Path to the main project directory.",
        required=True,
    )
    parser.add_argument(
        "--task",
        choices=[
            "feature-extraction",
            "code-analysis",
            "test-analysis",
            "code-summary",
        ],
        help="Task to run.",
        required=True,
    )
    parser.add_argument(
        "--only-file",
        help="Run the task only on this file.",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    sys.exit(main())
