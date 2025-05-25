from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class FeatureItem(BaseModel):
    name: str = Field(description="A short name or title for the feature.")
    description: str = Field(
        description="A clear description of what the feature is or does."
    )
    priority: Literal["High", "Medium", "Low"] = Field(
        description="Testing priority for this feature: High, Medium, or Low.",
        enum=["High", "Medium", "Low"],
    )
    is_unique: bool = Field(
        description="True if the feature is unique or uncommon compared to similar projects."
    )
    is_likely_to_change: bool = Field(
        description="True if this feature is expected to evolve frequently."
    )
    critical_to_user_experience: bool = Field(
        description="True if this feature is critical for user experience."
    )
    edge_cases_to_test: Optional[List[str]] = Field(
        description="List of edge cases or failure scenarios to consider for this feature."
    )


class ProjectFeatureAnalysis(BaseModel):
    project_name: str = Field(
        description="The official or working name of the software project."
    )
    project_description: str = Field(
        description="The full description or summary of the project."
    )
    main_goals: List[str] = Field(
        description="The main goals or objectives the project is trying to achieve."
    )
    similar_projects: List[str] = Field(
        description="Other tools, libraries, or projects that serve a similar purpose."
    )
    expected_features: List[str] = Field(
        description="Features that a typical user would expect from the project."
    )
    features: List[FeatureItem] = Field(
        description="A list of structured feature records."
    )
    edge_case_notes: Optional[List[str]] = Field(
        description="System-wide or project-level edge cases worth testing."
    )
