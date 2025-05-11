import os
from fcoverage.tasks import FeatureExtractionTask
import pytest
from unittest.mock import MagicMock, mock_open, patch
from langchain_core.prompt_values import HumanMessage, ChatPromptValue

PROMPT_TEMPLATE = """blah blah blah

**Project name:** {project_name}

**Project description:** {project_description}

**Documents:**

{documents}
"""


@pytest.fixture
def set_env(config):
    os.environ[config["llm-api-key-env-var"]] = "your_api_key"


@pytest.fixture
def args():
    return {
        "project": "test_project",
        "github": "https://github.com/octocat/Hello-World",
        "prompts-directory": "prompts",
    }


@pytest.fixture
def config():
    return {
        "documents": ["doc1.txt", "doc2.txt"],
        "prompts-directory": "prompts",
        "llm-model": "gemini-2.0-flash",
        "llm-model-provider": "openai",
        "llm-api-key-env-var": "LLM_API_KEY",
    }


@pytest.fixture
def mock_open_files(args, config):
    # Mock file contents for multiple files
    def side_effect_for_open(filename, *argsx, **kwargsx):
        if filename == f"{args['project']}/doc1.txt":
            return mock_open(read_data="Content of doc1")()
        elif filename == f"{args['project']}/doc2.txt":
            return mock_open(read_data="Content of doc2")()
        elif (
            filename
            == f"{args['project']}/{config['prompts-directory']}/feature_extraction.txt"
        ):
            return mock_open(read_data=PROMPT_TEMPLATE)()
        else:
            raise FileNotFoundError(f"File {filename} not found.")

    with patch("builtins.open") as mock_file:
        mock_file.side_effect = side_effect_for_open
        yield mock_file  # Provide the mock to the test


@pytest.fixture
def mock_llm():
    with patch("fcoverage.utils.llm.init_chat_model", autospec=True) as mock_init:
        # Set up the mock to return a mocked chat model
        mock_chat_model = MagicMock()
        mock_init.return_value = mock_chat_model
        mock_chat_model.invoke = MagicMock(return_value="Mocked LLM Response")
        yield mock_init, mock_chat_model  # Provide both the mock function and the mock model to the test


def test_ask_question(
    args, config, mock_open_files, set_env, mock_llm, mock_requests_get_github
):
    _, mock_chat_model = mock_llm

    task = FeatureExtractionTask(args, config)
    task.prepare()
    response = task.invoke_llm()

    expected_prompt = PROMPT_TEMPLATE.format(
        project_name="Hello-World",
        project_description="This your first repo!",
        documents="doc1.txt\nContent of doc1\n\ndoc2.txt\nContent of doc2",
    )

    assert response == "Mocked LLM Response"  # Verify the mocked return value
    mock_chat_model.invoke.assert_called_once_with(
        ChatPromptValue(
            messages=[
                HumanMessage(
                    content=expected_prompt,
                    additional_kwargs={},
                    response_metadata={},
                )
            ]
        )
    )
