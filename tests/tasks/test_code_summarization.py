import pytest
from fcoverage.tasks import CodeSummarizationTask
from fcoverage.models.code_summary import (
    ModuleSummary,
    ComponentSummary,
    FeatureMapping,
)
from fcoverage.utils.code.python_utils import CodeType


@pytest.fixture
def object_under_test(args, config):
    return CodeSummarizationTask(args, config)


@pytest.fixture
def file_path():
    return "foo/baz.py"


@pytest.fixture
def chunks(
    file_path,
    component_summary_item_1,
    component_summary_item_2,
    component_summary_item_3,
):
    return {
        f"{file_path}::{component_summary_item_1.name}": {"hash": "fake_hash_1"},
        f"{file_path}:{component_summary_item_2.name}": {"hash": "fake_hash_2"},
        f"{file_path}:{component_summary_item_3.name}": {"hash": "fake_hash_3"},
    }


@pytest.fixture
def module_summary_item(
    component_summary_item_1, component_summary_item_2, component_summary_item_3
):
    return ModuleSummary(
        summary="A summary of module",
        exports=["Bar"],
        features_mapping=[
            FeatureMapping(
                feature_name="random generator",
                confidence="Low",
            )
        ],
        imports=["datetime", "os", "foo_factory"],
        components=[
            component_summary_item_1,
            component_summary_item_2,
            component_summary_item_3,
        ],
    )


@pytest.fixture
def component_summary_item_1():
    return ComponentSummary(
        name="foo",
        type=CodeType.FUNCTION,
        summary="Summary of foo",
        imports=["os", "foo_factory"],
        features_mapping=[
            FeatureMapping(
                feature_name="pytest fixture",
                confidence="High",
            )
        ],
        tags=["important"],
    )


@pytest.fixture
def component_summary_item_2():
    return ComponentSummary(
        name="Bar",
        type=CodeType.CLASS,
        summary="Summary of bar",
        imports=["datetime"],
        features_mapping=[
            FeatureMapping(
                feature_name="random generator",
                confidence="Low",
            )
        ],
        tags=["complex"],
    )


@pytest.fixture
def component_summary_item_3():
    return ComponentSummary(
        name="Bar:buzz",
        type=CodeType.CLASS_METHOD,
        summary="Summary of buzz from Bar",
        imports=["datetime"],
        features_mapping=[
            FeatureMapping(
                feature_name="random generator",
                confidence="Low",
            )
        ],
        tags=["complex"],
    )


def test_summary_to_document(object_under_test, module_summary_item):
    documents = object_under_test.summary_to_document(module_summary_item)
    assert len(documents) == 4
    for doc in documents:
        assert "chunk_type" in doc.metadata
        assert "summary" not in doc.metadata
        assert "id" not in doc.metadata
        assert "type" in doc.metadata
        assert doc.metadata["chunk_type"] == object_under_test.CHUNK_TYPE
    assert documents[-1].metadata["type"] == "module"


def test_add_components_unique_ids(
    object_under_test, module_summary_item, chunks, file_path
):
    documents = object_under_test.summary_to_document(module_summary_item)
    object_under_test.add_components_unique_ids(file_path, documents[:-1], chunks)
    for doc in documents[:-1]:
        assert "id" in doc.metadata
        assert doc.metadata["id"] in [c["hash"] for c in chunks.values()]
