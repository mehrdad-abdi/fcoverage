import os
import pytest
import git
import tempfile
import shutil
import pathlib
from pymongo import MongoClient
import yaml


@pytest.fixture(scope="session")
def target_project():
    return "https://github.com/mehrdad-abdi/youtube-dl"


@pytest.fixture(scope="session")
def example_config_path():
    fcoverage_home = pathlib.Path(__file__).parent.parent.parent.resolve()
    return os.path.join(fcoverage_home, "target-repository-files", "config-example.yml")


@pytest.fixture(scope="session")
def mongo_db_connection():
    return "mongodb://localhost:27017/"


@pytest.fixture(scope="session")
def mongo_db_database():
    return "fcoverage-tests"


@pytest.fixture(scope="session")
def prepare_project(
    llm_api_key,
    target_project,
    clone_project_path,
    example_config_path,
    mongo_db_database,
):
    repo = git.Repo.clone_from(target_project, clone_project_path)
    fcoverage_dir = os.path.join(clone_project_path, ".fcoverage")
    os.mkdir(fcoverage_dir)
    config_file_path = os.path.join(fcoverage_dir, "config.yml")
    shutil.copyfile(example_config_path, config_file_path)

    with open(config_file_path, "r") as f:
        config = yaml.safe_load(f)
    config["source"] = "youtube_dl"
    config["mongo-db-database"] = "fcoverage-tests"
    with open(config_file_path, "w") as f:
        f.write(yaml.dump(config))

    return repo


@pytest.fixture(scope="session")
def mongo_db(prepare_project, mongo_db_connection, mongo_db_database):
    client = MongoClient(mongo_db_connection)
    db = client[mongo_db_database]
    yield db
    client.drop_database(mongo_db_database)


@pytest.fixture(scope="session")
def clone_project_path(llm_api_key, target_project):
    with tempfile.TemporaryDirectory(prefix="fcoverage_target_repo_") as temp_dir:
        yield temp_dir


@pytest.fixture(scope="session")
def artifacts_path(llm_api_key):
    fcoverage_home = pathlib.Path(__file__).parent.parent.parent.resolve()
    path = os.path.join(fcoverage_home, "test_artifacts")
    if not os.path.exists(path):
        os.mkdir(path)
    return path


@pytest.fixture(scope="session")
def llm_api_key():
    """I'm using google-genai because it provides free service for older models."""
    api_key = os.environ.get("LLM_API_KEY", None)
    if not api_key:
        pytest.skip("Acceptance test ignored because no LLM_API_KEY found.")
    os.environ["GOOGLE_API_KEY"] = api_key
    return api_key
