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


@pytest.fixture
def a_component(
    request,
    component,
):
    return request.getfixturevalue(component)


def test_summary_to_document_module(object_under_test, module_summary_item):
    doc = object_under_test.module_summary_to_document(module_summary_item, "hash")

    assert "source" in doc.metadata
    assert "summary" not in doc.metadata
    assert "id" in doc.metadata
    assert "code_type" in doc.metadata
    assert doc.metadata["source"] == object_under_test.CHUNK_SOURCE
    assert doc.metadata["code_type"] == CodeType.MODULE


@pytest.mark.parametrize(
    "component",
    [
        "component_summary_item_1",
        "component_summary_item_2",
        "component_summary_item_3",
    ],
)
def test_summary_to_document_components(object_under_test, a_component):
    doc = object_under_test.component_summary_to_document(a_component, hash)
    assert "source" in doc.metadata
    assert "summary" not in doc.metadata
    assert "id" in doc.metadata
    assert "code_type" in doc.metadata
    assert doc.metadata["source"] == object_under_test.CHUNK_SOURCE
    assert doc.metadata["code_type"] in [
        CodeType.CLASS,
        CodeType.FUNCTION,
        CodeType.CLASS_METHOD,
    ]
