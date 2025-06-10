import os
import shutil
from unittest.mock import patch
import pytest
import fcoverage


@pytest.fixture
def patch_main(test_argv):
    with patch("sys.argv", test_argv):
        fcoverage.main.main()


@pytest.fixture
def test_argv(clone_project_path, target_project):
    return [
        "fcoverage",
        "--task",
        "feature-extraction",
        "--gitthub",
        target_project,
        "--project",
        clone_project_path,
    ]


def test_feature_extraction(
    patch_main,
    prepare_project,
    clone_project_path,
    llm_api_key,
    target_project,
    artifacts_path,
):
    assert os.path.exists(
        os.path.join(clone_project_path, ".fcoverage", "feature-list.md")
    )
    assert os.path.exists(
        os.path.join(clone_project_path, ".fcoverage", "project-features.json")
    )

    # keep files as test artifacts
    shutil.copyfile(
        os.path.join(clone_project_path, ".fcoverage", "feature-list.md"),
        os.path.join(artifacts_path, "feature-list.md"),
    )
    shutil.copyfile(
        os.path.join(clone_project_path, ".fcoverage", "project-features.json"),
        os.path.join(artifacts_path, "project-features.json"),
    )
