from typing import List
from pydantic import BaseModel, Field


class FeatureManifest(BaseModel):
    name: str
    description: str
    entry_point: str
    related_test_files: List[str]
    core_code_files: List[str]


class FeatureItem(BaseModel):
    name: str = Field(description="A short name or title for the feature.")
    description: str = Field(
        description="Provide a clear and complete explanation and answer these questions for the feature: what the feature is, how it works, who it is for, and the value it provides. Include all important details and use complete sentences that are informative, avoiding overly brief explanations."
    )
    entry_point: str = Field(
        description="A description of how a user might access this feature (e.g., 'Through the 'Export' button on the user profile page', or 'Via the `/api/v2/report` endpoint'). If unknown, state 'Unknown'."
    )
    keywords: List[str] = Field(
        description="list of relevant searchable keywords. You expect to see these keywords in the name of related files, classes, methods, functions. To be used in find or grep to discover these code portions.",
    )
    queries: List[str] = Field(
        description="list of relevant RAG queries to use similarity search for retrieve related production code.",
    )


class ProjectFeatures(BaseModel):
    features: List[FeatureItem] = Field(
        description="A list of structured feature records."
    )


class TestToFeatures(BaseModel):
    related_features: List[str] = Field(
        description="The list of feature names (exact name according the List of features) that the test tries to cover. Leave it empty if you couldn't relate the test to any feature."
    )
