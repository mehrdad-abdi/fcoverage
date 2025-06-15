from pydantic import BaseModel, Field
from typing import List, Optional, Literal

from fcoverage.utils.code.python_utils import CodeType


class FeatureMapping(BaseModel):
    feature_name: str = Field(description="The exact name of the feature.")
    confidence: Literal["High", "Medium", "Low"] = Field(
        description="The level of confidence of this relation."
    )


class TestMethodSummary(BaseModel):
    name: str = Field(
        description="name of the component. If it's a class method use `class_name:method_name` format."
    )
    type: CodeType = Field(
        description="whether it's a function/class/method.",
    )
    summary: str = Field(
        description="A clear description of what it does. Description of key logic, behaviors, or edge cases. For methods: how they relate to the enclosing class or other methods. Do not include unnecessary information.",
        max_length=500,
    )
    imports: List[str] = Field(
        description="Any imports that relates this code to any other code."
    )
    features_mapping: Optional[List[FeatureMapping]] = Field(
        description="If you have been asked to map the component to project features, list related features here."
    )
    tags: List[str] = Field(
        description="Assign relevant tags like complex, important and external-dependency."
    )


class TestUtilsSummary(BaseModel):
    name: str = Field(
        description="name of the component. If it's a class method use `class_name:method_name` format."
    )
    type: CodeType = Field(
        description="whether it's a function/class/method.",
    )
    summary: str = Field(
        description="A clear description of what it does. Description of key logic, behaviors, or edge cases. For methods: how they relate to the enclosing class or other methods. Do not include unnecessary information.",
        max_length=500,
    )
    imports: List[str] = Field(
        description="Any imports that relates this code to any other code."
    )


class TestUtilsFileSummary(BaseModel):
    components: List[TestUtilsSummary] = Field(
        description="Summary of each function/class/method/fixture."
    )


class TestFileSummary(BaseModel):
    summary: str = Field(
        description="A description of the overall purpose of the code and the main functionalities.",
        max_length=500,
    )
    imports: List[str] = Field(
        description="Any imports that relates this code to any other code."
    )
    test_methods: List[TestMethodSummary] = Field(
        description="Summary for each test method in the file."
    )
    features_mapping: Optional[List[FeatureMapping]] = Field(
        description="If you have been asked to map the file to project features, list related features here."
    )
