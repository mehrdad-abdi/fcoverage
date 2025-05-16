from fcoverage.tasks import SourceCodeEmbeddingTask


def test_ask_question(
    args, config, mock_open_files, mock_llm, mock_requests_get_github
):
    _, mock_chat_model = mock_llm

    task = SourceCodeEmbeddingTask(args, config)
    task.prepare()
    response = task.invoke_llm()
