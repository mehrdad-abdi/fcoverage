import yaml
import argparse
import os
from fcoverage.tasks import (
    FeatureExtractionTask,
    TestAnalysisTask,
    ReportGenerationTask,
)


DEFAULT_HOME = ".fcoverage"
DEFAULT_CONFIG_PATH = f"{DEFAULT_HOME}/config.yml"


def load_config(project_path):
    """
    Loads the YAML configuration file.

    Args:
        project_path (str): The path to the project directory.

    Returns:
        dict: The loaded configuration.

    Raises:
        FileNotFoundError: If the config file is not found.
        yaml.YAMLError: If there's an error parsing the YAML.
    """

    config_file_path = os.path.join(os.path.abspath(project_path), DEFAULT_CONFIG_PATH)
    print(f"Attempting to load configuration from: {config_file_path}")
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(
            f"Configuration file not found: {os.path.abspath(config_file_path)}"
        )
    with open(config_file_path, "r") as f:
        config = yaml.safe_load(f)
    print("Configuration loaded successfully:")
    return config


def main():
    args = get_args()

    try:
        config = load_config(args.project)
        print(yaml.dump(config, indent=2))

        FeatureExtractionTask(config=config).run()
        TestAnalysisTask(config=config).run()
        ReportGenerationTask(config=config).run()

    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error: {e}")


def get_args():
    parser = argparse.ArgumentParser(description="Feature Coverage Analysis Tool")
    parser.add_argument(
        "--project",
        type=str,
        help=f"Path to the main project directory.",
        required=True,
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
