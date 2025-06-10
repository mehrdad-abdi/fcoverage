import shutil
import subprocess
import pytest
import os
from unittest.mock import patch

import fcoverage
import fcoverage.main
import chromadb


@pytest.fixture
def python_file(prepare_project, clone_project_path):
    return os.path.join(clone_project_path, "youtube_dl", "update.py")


@pytest.fixture
def patch_main(test_argv, add_a_feature_file):
    with patch("sys.argv", test_argv):
        fcoverage.main.main()


@pytest.fixture
def test_argv(clone_project_path, python_file):
    return [
        "fcoverage",
        "--task",
        "code-summary",
        "--only-file",
        python_file,
        "--project",
        clone_project_path,
    ]


@pytest.fixture
def add_a_feature_file(clone_project_path):
    filename_json = os.path.join(clone_project_path, ".fcoverage", "feature-list.md")
    with open(filename_json, "w") as f:
        f.write(
            """# Features List

## Features

### 1. Video Download: *Downloading videos from various platforms (YouTube, etc.)*
### 2. Format Selection: *Selecting specific video formats and qualities*
### 3. Update Program: *Updating the program*

"""
        )


@pytest.fixture
def mongo_collection_name():
    return "code-summary"


def test_summary_file(
    patch_main,
    prepare_project,
    clone_project_path,
    llm_api_key,
    target_project,
    artifacts_path,
    python_file,
    mongo_db_connection,
    mongo_db_database,
    mongo_collection_name,
    mongo_db,
):
    assert os.path.exists(
        os.path.join(clone_project_path, ".fcoverage", "vdb", "chroma.sqlite3")
    )
    client = chromadb.PersistentClient(
        os.path.join(clone_project_path, ".fcoverage", "vdb")
    )
    assert "fcoverage" in [c.name for c in client.list_collections()]
    vdb_collection = client.get_collection("fcoverage")
    assert vdb_collection.count() > 0

    # keep files as test artifacts
    shutil.copytree(
        os.path.join(clone_project_path, ".fcoverage", "vdb"),
        os.path.join(artifacts_path, "vdb"),
        dirs_exist_ok=True,
    )

    assert mongo_db[mongo_collection_name].count_documents({}) > 0
    assert mongo_db[mongo_collection_name].count_documents({}) == vdb_collection.count()

    subprocess.run(
        f"mongodump --uri=\"{mongo_db_connection}\" --db={mongo_db_database} --collection={mongo_collection_name} --out={os.path.join(artifacts_path, 'mongodb')}",
        shell=True,
    )
