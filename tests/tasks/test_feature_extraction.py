from fcoverage.models.feature_list import FeatureItem, ProjectFeatureAnalysis
from fcoverage.tasks import FeatureCatalogTask
import pytest


@pytest.fixture
def object_under_test(args, config):
    return FeatureCatalogTask(args, config)


@pytest.fixture
def feature_item():
    return FeatureItem(
        name="csv support",
        critical_to_user_experience=True,
        description="Saves and Opens csv files",
        is_unique=False,
        is_likely_to_change=True,
        priority="Medium",
        edge_cases_to_test=None,
    )


@pytest.fixture
def features(feature_item):
    return ProjectFeatureAnalysis(
        project_name="Test Project",
        project_description="Fake project description",
        edge_case_notes=["Some edge items"],
        expected_features=[
            "Should work",
            "Should terminate",
        ],
        main_goals=["Shows our project work", "It doesn't do more."],
        similar_projects=["foo", "bar"],
        features=[feature_item],
    )


def test_markdown_creation(object_under_test, feature_item):
    md_output = object_under_test.feature_item_to_markdown(18, feature_item)

    assert (
        md_output
        == """### 18. csv support

*Saves and Opens csv files*

Testing priority for this feature: **Medium**

[**critical** for user experience]  [likely to **evolve** frequently]


"""
    )


def test_features_to_markdown(object_under_test, features: ProjectFeatureAnalysis):
    md_output = object_under_test.features_to_markdown(features)

    assert "Shows our project work" in md_output
    assert "foo" in md_output
    assert "bar" in md_output
    assert "It doesn't do more." in md_output
    assert "Some edge items" in md_output
    assert "Fake project description" in md_output
    assert "Test Project" in md_output
    assert "Saves and Opens csv files" in md_output
    assert "csv support" in md_output
    assert "Medium" in md_output
