from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class FeatureMapping(BaseModel):
    feature_name: str = Field(description="The exact name of the feature.")
    confidence: Literal["High", "Medium", "Low"] = Field(
        description="The level of confidence of this relation."
    )


class ComponentSummary(BaseModel):
    name: str = Field(description="name of the component.")
    type: Literal["Function", "Class", "Class method", "Other"] = Field(
        description="whether it's a function/class/method. If the component is not a function/class/method, but it's important to be noticed in the summary, use Other",
        enum=["Function", "Class", "Class method", "Other"],
    )
    summary: str = Field(description="A clear description of what it does.")
    details: str = Field(
        description="Description of key logic, behaviors, or edge cases. For methods: how they relate to the enclosing class or other methods."
    )
    imports: List[str] = Field(
        description="Any imports that relates this code to any other code within the project."
    )
    features_mapping: Optional[List[FeatureMapping]] = Field(
        description="If you have been asked to map the component to project features, list related features here."
    )


class ModuleSummary(BaseModel):
    summary: str = Field(
        description='A short description of the overall purpose of the code and the main functionalities. Keep it concise; detailed insights should go in the "details" field.'
    )
    details: str = Field(
        description="Any other notable design decisions, patterns, or libraries used."
    )
    imports: List[str] = Field(
        description="Any imports that relates this code to any other code within the project."
    )
    exports: List[str] | None = Field(
        description="If it's a module, mention the exported symbols."
    )
    components: List[ComponentSummary] = Field(
        description="Summary for each component in the file."
    )
    features_mapping: Optional[List[FeatureMapping]] = Field(
        description="If you have been asked to map the file to project features, list related features here."
    )
