import os
import shutil
import subprocess


def test_feature_extraction(
    prepare_project, clone_project_path, llm_api_key, target_project, artifacts_path
):
    subprocess.run(
        [
            "fcoverage",
            "--task",
            "feature-extraction",
            "--gitthub",
            target_project,
            "--project",
            clone_project_path,
        ],
        env=os.environ,
    )

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
