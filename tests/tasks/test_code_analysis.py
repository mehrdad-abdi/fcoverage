import json
import os
import shutil
from unittest.mock import MagicMock, patch
import pytest
from fcoverage.tasks import CodeAnalysisTask


@pytest.fixture
def mock_embedding():
    with patch("fcoverage.utils.llm.init_embeddings", autospec=True) as mock_init:
        # Set up the mock to return a mocked chat model
        mock_embeddings = MagicMock()
        mock_init.return_value = mock_embeddings
        mock_embeddings.embed_documents = MagicMock(
            return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        )
        yield mock_init, mock_embeddings  # Provide both the mock function and the mock model to the test


@pytest.fixture
def mock_faiss():
    with patch("fcoverage.tasks.code_analysis.FAISS", autospec=True) as mock_faiss:
        # Set up the mock to return a mocked chat model
        yield mock_faiss


@pytest.fixture
def ensure_project_directory_is_clean(args, config):
    rag_save_location = os.path.join(args["project"], config["rag-save-location"])
    if os.path.exists(rag_save_location):
        shutil.rmtree(rag_save_location)
    yield
    if os.path.exists(rag_save_location):
        shutil.rmtree(rag_save_location)


@pytest.fixture
def create_vector_db(
    args, config, mock_embedding, mock_faiss, ensure_project_directory_is_clean
):
    task = CodeAnalysisTask(args, config)
    task.prepare()
    task.run()
    # Create a fake index file to simulate the initial RAG
    os.makedirs(task.rag_save_location, exist_ok=True)
    with open(task.faiss_index_path, "w") as f:
        f.write("FAISS index data")
    yield
    # Clean up the fake index file after the test
    if os.path.exists(task.faiss_index_path):
        os.remove(task.faiss_index_path)


@pytest.fixture
def update_a_source_code_file(
    args, config, create_vector_db, ensure_project_directory_is_clean
):
    target_file = os.path.join(args["project"], config["source"], "dummy/utils/util.py")
    new_file = os.path.join(args["project"], config["source"], "dummy/dummy_file.py")
    try:
        # Create a dummy file to simulate the update
        with open(new_file, "w") as f:
            f.write("def new_function():\n    return 'new'\n")
        # Update exiting file: deletes a method and adds a new one
        with open(target_file, "r") as f:
            content = f.read()
        content = content.replace("def greet", "def greet_edited")
        with open(target_file, "w") as f:
            f.write(content)
        yield target_file, new_file
    finally:
        # Clean up the file after the test
        os.remove(new_file)
        with open(target_file, "r") as f:
            content = f.read()
        # Revert the changes made to the file
        content = content.replace("def greet_edited", "def greet")
        with open(target_file, "w") as f:
            f.write(content)


def test_no_faiss(
    args, config, mock_embedding, mock_faiss, ensure_project_directory_is_clean
):
    mock_init, mock_embedding = mock_embedding

    task = CodeAnalysisTask(args, config)
    task.prepare()
    result = task.run()

    assert result is True
    assert len(task.documents) == 15

    test_chunks = [
        doc
        for doc in task.documents.values()
        if doc.metadata["chunk_type"] == "test_code"
    ]
    code_chunks = [
        doc
        for doc in task.documents.values()
        if doc.metadata["chunk_type"] == "source_code"
    ]
    assert all(
        ["covers" in doc.metadata for doc in test_chunks]
    ), "All test code chunks should have 'covers' metadata"
    assert all(
        ["fixture_requests" in doc.metadata for doc in test_chunks]
    ), "All test code chunks should have 'fixture_requests' metadata"
    assert all(
        ["fixture_requested_by" in doc.metadata for doc in test_chunks]
    ), "All test code chunks should have 'fixture_requested_by' metadata"
    assert all(
        ["covered_by" in doc.metadata for doc in code_chunks]
    ), "All source code chunks should have 'covered_by' metadata"

    mock_faiss.from_documents.assert_called_once()
    assert mock_faiss.from_documents.call_args[0][0] == list(task.documents.values())
    assert mock_faiss.from_documents.call_args[0][1] == mock_embedding
    mock_vdb = mock_faiss.from_documents.return_value
    mock_vdb.save_local.assert_called_once()
    assert mock_vdb.save_local.call_args[0][0] == task.rag_save_location

    with open(task.meta_data_path, "r") as f:
        metadata = json.load(f)
        assert len(metadata) == 15


def test_update_faiss(
    args,
    config,
    mock_embedding,
    mock_faiss,
    create_vector_db,
    update_a_source_code_file,
    ensure_project_directory_is_clean,
):
    updated_file, added_file = update_a_source_code_file
    mock_init, mock_embedding = mock_embedding
    # The fixtuer create_initial_rag should have already created the initial RAG
    # The fixture update_a_source_code_file should have updated the source code file
    # We call the task again to update the RAG
    task = CodeAnalysisTask(args, config)
    task.prepare()
    result = task.run()

    assert result is True
    assert len(task.documents) == 16
    mock_faiss.load_local.assert_called_once()
    mock_vdb = mock_faiss.load_local.return_value
    mock_vdb.add_documents.assert_called_once()
    assert (
        len(mock_vdb.add_documents.call_args[0][0]) == 2
    ), "Expects exactly 2 documents to be added"
    mock_vdb.delete.assert_called_once()
    assert (
        len(mock_vdb.delete.call_args[0][0]) == 1
    ), "Expects exactly 1 document to be deleted"
    mock_vdb.save_local.assert_called_once()
    assert mock_vdb.save_local.call_args[0][0] == task.rag_save_location


@pytest.mark.integration
@pytest.mark.parametrize(
    "config",
    [
        {
            "rag-save-location": ".fcoverage/rag",
            "source": "src",
            "tests": "tests",
            "embedding": {
                "provider": "offline",
                "model": "sentence-transformers/all-MiniLM-L6-v2",
            },
        }
    ],
    ids=["all-MiniLM-L6-v2"],
)
def test_offline_embedding(args, config, ensure_project_directory_is_clean):
    task = CodeAnalysisTask(args, config)
    task.prepare()
    result = task.run()

    assert result is True

    doc = task.vectorstore.similarity_search(
        "How many processors do I have?", k=1, filter={"chunk_type": "source_code"}
    )
    assert len(doc) == 1
    assert "os.cpu_count" in doc[0].page_content

    doc = task.vectorstore.similarity_search(
        "How can I use Calculator class?", k=1, filter={"chunk_type": "source_code"}
    )
    assert len(doc) == 1
    assert "run_calculator" in doc[0].page_content
