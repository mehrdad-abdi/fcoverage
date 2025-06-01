from fcoverage.tasks import FeatureExtractionTask
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.prompt_values import HumanMessage, ChatPromptValue

PROMPT_TEMPLATE = """blah blah blah

**Project name:** {project_name}

**Project description:** {project_description}

**Documents:**

{documents}"""


@pytest.fixture
def mock_llm():
    with patch(
        "fcoverage.tasks.feature_extraction.init_chat_model", autospec=True
    ) as mock_init:
        # Set up the mock to return a mocked chat model
        mock_chat_model = MagicMock()
        mock_init.return_value = mock_chat_model
        mock_chat_model.invoke = MagicMock(return_value="Mocked LLM Response")
        yield mock_init, mock_chat_model  # Provide both the mock function and the mock model to the test


def test_ask_question(
    args,
    config,
    mock_llm,
    mock_requests_get_github,
):
    _, mock_chat_model = mock_llm

    task = FeatureExtractionTask(args, config)
    task.prepare()
    response = task.invoke_llm()

    expected_prompt = PROMPT_TEMPLATE.format(
        project_name="dummy_project",
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
