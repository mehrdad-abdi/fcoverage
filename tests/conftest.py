import os
import pytest
from unittest.mock import patch
import yaml


@pytest.fixture
def args():
    current_file_path = os.path.abspath(__file__)
    current_file_directory = os.path.dirname(current_file_path)

    return {
        "project": f"{current_file_directory}/dummy_project",
        "github": "https://github.com/acme/dummy_project",
    }


@pytest.fixture
def config(args):
    with open(args["project"] + "/.fcoverage/config.yml", "r") as f:
        config = yaml.safe_load(f)
    return config


@pytest.fixture
def mock_requests_get_github():
    with patch("fcoverage.utils.http.requests.get") as mock_get:
        # Mock response object
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "owner": {"login": "acme"},
            "name": "dummy_project",
            "description": "This your first repo!",
        }
        yield mock_get  # Provide the mock to the test
