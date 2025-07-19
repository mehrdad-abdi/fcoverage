import os
import sys
import argparse
from fcoverage.tasks import (
    FeatureExtractionTask,
    FeatureDesignTask,
    FeatureCoverageTask,
)


def main():
    args = get_args()
    os.makedirs(args["out"], exist_ok=True)

    if args["task"] == "extract":
        task = FeatureExtractionTask(args=args)
    elif args["task"] == "design":
        task = FeatureDesignTask(args=args)
    elif args["task"] == "coverage":
        task = FeatureCoverageTask(args=args)
    task.prepare()
    return task.run()


def get_args():
    parser = argparse.ArgumentParser(description="Feature Coverage Analysis Tool")
    parser.add_argument(
        "--project-name",
        type=str,
        help="The name of the project.",
        required=True,
    )
    parser.add_argument(
        "--project-description",
        type=str,
        help="The project description.",
        required=True,
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
            "extract",
            "design",
            "coverage",
        ],
        help="Task to run.",
        required=True,
    )
    parser.add_argument(
        "--out",
        help="Output folder.",
        default="fcoverage",
    )
    parser.add_argument(
        "--vector-db-persist",
        help="The path to store the vector database.",
        default="vector-db",
    )
    parser.add_argument(
        "--src-path",
        help="The folder containing source codes within the project root.",
        default="src",
    )
    parser.add_argument(
        "--test-path",
        help="The folder containing test codes within the project root.",
        default="test",
    )
    parser.add_argument(
        "--llm-model",
        help="The name of llm model. See https://python.langchain.com/docs/integrations/chat/.",
        default="gemini-2.0-flash",
    )
    parser.add_argument(
        "--llm-provider",
        help="The name of llm model provider. See https://python.langchain.com/docs/integrations/chat/.",
        default="google_genai",
    )
    parser.add_argument(
        "--embedding-model",
        help="The name of embedding model. See https://python.langchain.com/docs/integrations/chat/.",
        default="text-embedding-3-large",
    )
    parser.add_argument(
        "--embedding-provider",
        help="The name of llm embedding provider. See https://python.langchain.com/docs/integrations/chat/.",
        default="openai",
    )
    parser.add_argument(
        "--docs",
        help="List of documentation files, within the project root, which features list will be extacted from.",
        default=[],
        nargs="+",
    )
    parser.add_argument(
        "--feature-definition",
        help="The path of feature definition file. Required in design and coverage tasks.",
        default="",
    )
    parser.add_argument(
        "--feature-design",
        help="The path of feature design file. Required in coverage task.",
        default="",
    )
    parser.add_argument(
        "--feature-test-cases",
        help="The path of feature test-case file. Required in coverage task.",
        default="",
    )
    parser.add_argument(
        "--max-features",
        help="The max number of features to be extracted in extraction task.",
        type=int,
        default=10,
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    sys.exit(main())
